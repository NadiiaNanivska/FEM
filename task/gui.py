import os
import logging
import numpy as np
import wx
import datetime

from task import constants
from task.windows.grid_result_viewer import GridResultsViewer
from task.windows.mge_viewer import MGEViewer
from task.windows.results_table_viewer import ResultsTableViewer
from task.dto.simulation_params import SimulationParams
from task.fem_functions.mesh_generator import MeshGenerator
from task.fem_functions.shape_functions import ShapeFunctionsMath
from task.windows.mesh_vizualizer import MeshVisualizer
from task.fem_functions.boundary_condition_manager import BoundaryConditionManager
from task.windows.depsite_f_viewer import DEPSITEandFViewer
from task.dto.simulation_results import SimulationResults
import ctypes
import threading
from wx.lib.newevent import NewEvent

from task.windows.stress_isosurface_viewer import (
    IsoSurfaceDialog, MeshScaleDialog, build_isosurface_figure
)
from task.windows.akt_nt_viewer import AktNtViewer

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


CalculationStepEvent, EVT_CALCULATION_STEP = NewEvent()
CalculationDoneEvent, EVT_CALCULATION_DONE = NewEvent()
CalculationErrorEvent, EVT_CALCULATION_ERROR = NewEvent()

# Грані елемента (1-based): номер → (вісь, сторона)
FACE_MAP = {
    1: (0, 'min'),
    2: (0, 'max'),
    3: (1, 'min'),
    4: (1, 'max'),
    5: (2, 'min'),
    6: (2, 'max'),
}
FACE_CHOICES = ["1 — X мін", "2 — X макс", "3 — Y мін", "4 — Y макс", "5 — Z мін", "6 — Z макс"]


class ZPPanel(wx.Panel):
    """
    Динамічна таблиця ZP: кожен рядок — індекс елемента + грань навантаження.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._rows = [] 

        self._main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Заголовок таблиці
        hdr = wx.BoxSizer(wx.HORIZONTAL)
        lbl_el = wx.StaticText(self, label="Елем.")
        lbl_face = wx.StaticText(self, label="Грань")
        hdr.Add(lbl_el, 0, wx.RIGHT, 55)
        hdr.Add(lbl_face, 0)
        self._main_sizer.Add(hdr, 0, wx.LEFT | wx.TOP, 2)

        self._rows_sizer = wx.BoxSizer(wx.VERTICAL)
        self._main_sizer.Add(self._rows_sizer, 0, wx.EXPAND)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_btn = wx.Button(self, label="+ рядок", size=(90, 26))
        self._del_btn = wx.Button(self, label="− видалити", size=(90, 26))
        btn_sizer.Add(self._add_btn, 0, wx.RIGHT, 6)
        btn_sizer.Add(self._del_btn, 0)
        self._main_sizer.Add(btn_sizer, 0, wx.TOP, 4)

        self.SetSizer(self._main_sizer)

        self._add_btn.Bind(wx.EVT_BUTTON, lambda e: self._add_row())
        self._del_btn.Bind(wx.EVT_BUTTON, self._on_del)

        self._add_row("0", 5)  # дефолтний рядок: елемент 0, грань 6 (Z макс)

    def _add_row(self, el_val: str = "", face_sel: int = 5):
        row = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        el_ctrl = wx.TextCtrl(row, value=el_val, size=(60, 26))
        face_ctrl = wx.Choice(row, choices=FACE_CHOICES, size=(120, 26))
        face_ctrl.SetSelection(face_sel)

        sizer.Add(el_ctrl, 0, wx.RIGHT, 6)
        sizer.Add(face_ctrl, 0)
        row.SetSizer(sizer)

        self._rows.append((el_ctrl, face_ctrl, row))
        self._rows_sizer.Add(row, 0, wx.EXPAND | wx.BOTTOM, 3)
        self._refresh()

    def _on_del(self, event):
        if self._rows:
            _, _, row_panel = self._rows.pop()
            self._rows_sizer.Detach(row_panel)
            row_panel.Destroy()
            self._refresh()

    def _refresh(self):
        self._rows_sizer.Layout()
        self._main_sizer.Layout()
        self.Layout()
        p = self.GetParent()
        while p:
            p.Layout()
            if isinstance(p, wx.ScrolledWindow):
                p.FitInside()
                break
            p = p.GetParent()

    def get_entries(self):
        """Повертає список (element_idx, face_num_1based) для всіх рядків."""
        result = []
        for el_ctrl, face_ctrl, _ in self._rows:
            raw = el_ctrl.GetValue().strip()
            sel = face_ctrl.GetSelection()
            if not raw or sel < 0:
                continue
            try:
                result.append((int(raw), sel + 1))
            except ValueError:
                pass
        return result

    def set_entries(self, entries):
        """Заповнює таблицю зі списку (el_idx, face_num)."""
        while self._rows:
            _, _, p = self._rows.pop()
            self._rows_sizer.Detach(p)
            p.Destroy()
        for el_idx, face_num in entries:
            self._add_row(str(el_idx), face_num - 1)
        self._refresh()


class CalculationThread(threading.Thread):
    """
    Виконує весь МСЕ-пайплайн у фоновому потоці, щоб не блокувати GUI.

    Відповідає зведеному алгоритму МСЕ (заняття 13, практикум):
      1) Формування сітки: AKT, NT, ZU
      2) Передобчислення: DFIABG, потім для кожного елемента: J, |J|, DFIXYZ
      3) Матриці жорсткості елементів MGE (60×60)
      4) Вектори навантаження елементів FE (60×1)
      5) Асемблювання MG та F, граничні умови, розв'язок MG·U = F
      6) Обчислення напружень σ та головних напружень σ₁,σ₂,σ₃
    """

    def __init__(self, parent_window, params, results_obj):
        super().__init__()
        self.parent_window = parent_window
        self.params = params
        self.results = results_obj
        self.logger = logging.getLogger(__name__ + ".CalcThread")

    def run(self):
        """Виконується у фоновому потоці. Надсилає події GUI через wx.PostEvent."""
        try:
            mesh_gen = MeshGenerator()
            math_engine = ShapeFunctionsMath()
            bc_manager = BoundaryConditionManager()

            # ─────────────────────────────────────────────────────────────────
            # КРОК 1: ГЕНЕРАЦІЯ СІТКИ (заняття 1 і 3, формули 7, 21)
            # ─────────────────────────────────────────────────────────────────
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Генерація сітки...", progress=5))
            elements = mesh_gen.create_points(self.params.a, self.params.b, self.params.c, self.params.na, self.params.nb, self.params.nc)
            AKT = mesh_gen.separate_point(self.params.a, self.params.b, self.params.c, self.params.na, self.params.nb, self.params.nc)
            NT = mesh_gen.NT_transform(AKT, elements)
            self.results.AKT = AKT
            self.results.NT = NT

            ZU = []
            for idx in self.params.zu_node_indices:
                if 0 <= idx < len(AKT):
                    ZU.append(AKT[idx])
                else:
                    self.logger.warning(f"Вузол {idx} поза межами AKT (розмір {len(AKT)}) — пропущено")
            if not ZU:
                raise ValueError("Список закріплених вузлів ZU порожній — вкажіть коректні індекси.")
            self.logger.info(f"Закріплені вузли (ZU): {len(ZU)} вузлів")

            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Сітка згенерована.", progress=10, enable_btn='mesh'))

            # ─────────────────────────────────────────────────────────────────
            # КРОК 2: DFIABG, ЯКОБІАНИ, DFIXYZ (формули 27-29, 39-42)
            # ─────────────────────────────────────────────────────────────────
            # DFIABG[27,20,3]: ∂φᵢ/∂(α,β,γ) у 27 точках Гауса. Один раз для всіх.
            # Для кожного елемента:
            #   DJ[27][3×3] — матриці Якобі (формули 27, 40)
            #   DJ_det[27]  — |J| в кожній точці Гауса (формула 41)
            #   DFIXYZ[27,20,3] — ∂φᵢ/∂(x,y,z): J·DFIXYZ=DFIABG (формула 42)
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Обчислення Якобіанів та похідних...", progress=15))
            DFIABG = math_engine.DFIABG_Create()
            DJ, DJ_det, DFIXYZ = [], [], []

            total_els = len(NT)
            for i, element_coords in enumerate(elements):
                jacobians = math_engine.create_jacobian_for_element(element_coords, DFIABG)
                DJ.append(jacobians)

                det_j_for_element = [math_engine.calculate_determinant(J) for J in jacobians]
                DJ_det.append(det_j_for_element)

                dfixyz_element = math_engine.calculate_dfixyz_for_element(jacobians, DFIABG)
                DFIXYZ.append(dfixyz_element)

                if i % max(1, total_els // 10) == 0:
                    prog = 15 + int(20 * (i / total_els))
                    wx.PostEvent(self.parent_window, CalculationStepEvent(msg=f"Якобіани: елемент {i}/{total_els}", progress=prog))

            self.results.DJ = DJ
            self.results.DJ_det = DJ_det
            self.results.DFIXYZ = DFIXYZ

            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Якобіани обчислені.", progress=35, enable_btn='dj'))

            # ─────────────────────────────────────────────────────────────────
            # КРОК 3: МАТРИЦІ ЖОРСТКОСТІ ЕЛЕМЕНТІВ MGE (формули 15, 38, 43)
            # ─────────────────────────────────────────────────────────────────
            # Для кожного елемента будуємо MGE[60×60] через квадратуру Гауса (27 точок).
            # Параметри λ, ν, μ = G — параметри матеріалу (формула 6, заняття 1).
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Обчислення локальних матриць жорсткості (MGE)...", progress=40))
            list_of_MGE = []
            for i in range(len(elements)):
                list_of_MGE.append(
                    math_engine.calc_MGE(DFIXYZ[i], DJ_det[i], [constants.c_1, constants.c_2, constants.c_3],
                                         self.params.liambda, self.params.nu, self.params.mu))
                if i % max(1, total_els // 10) == 0:
                    prog = 40 + int(30 * (i / total_els))
                    wx.PostEvent(self.parent_window, CalculationStepEvent(msg=f"MGE: елемент {i}/{total_els}", progress=prog))

            self.results.MGE = list_of_MGE

            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="MGE обчислені.", progress=70, enable_btn='mge'))

            # ─────────────────────────────────────────────────────────────────
            # КРОК 4: ВЕКТОРИ НАВАНТАЖЕННЯ ЕЛЕМЕНТІВ FE (формули 44-45)
            # ─────────────────────────────────────────────────────────────────
            # FE[60]: вектор сил від тиску P на навантажену грань елемента.
            # Для кожного запису (el_idx, face_num) з ZP визначаємо яка грань
            # елемента навантажена і викликаємо FE_Calc.
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Формування векторів сил (FE)...", progress=75))
            gauss_weights_2d = [constants.c_1, constants.c_2, constants.c_3]
            nel = len(NT)

            FE = [np.zeros(60).tolist() for _ in range(nel)]

            for el_idx, face_num in self.params.zp_entries:
                if not (0 <= el_idx < nel):
                    self.logger.warning(f"Елемент {el_idx} поза межами [0, {nel-1}] — пропущено")
                    continue
                press_axis, press_side = FACE_MAP[face_num]
                element_nodes = [AKT[node_idx] for node_idx in NT[el_idx]]
                ZP_cast = bc_manager.ZP_Chose(element_nodes, press_axis, press_side)
                if len(ZP_cast) == 8:
                    FE[el_idx] = math_engine.FE_Calc(
                        gauss_weights_2d, self.params.P, ZP_cast,
                        press_axis=press_axis, press_side=press_side
                    )

            self.results.FE = FE

            # ─────────────────────────────────────────────────────────────────
            # КРОК 5: АСЕМБЛЮВАННЯ ТА РОЗВ'ЯЗАННЯ (заняття 8, 10, 11)
            # ─────────────────────────────────────────────────────────────────
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Ансамблювання MGG та розв'язання рівнянь...", progress=80))

            MGG = math_engine.MG_Create(list_of_MGE, len(AKT), NT, ZU, AKT)
            F   = math_engine.F_Create(FE, len(AKT), NT)

            displacements = np.linalg.solve(MGG, F)
            self.results.displacements = displacements

            # ─────────────────────────────────────────────────────────────────
            # КРОК 6: НАПРУЖЕННЯ (заняття 12, формули 48, 49)
            # ─────────────────────────────────────────────────────────────────
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Обчислення напружень...", progress=95))
            stresses = math_engine.calculate_stresses(displacements, self.params.E, self.params.nu, self.results)
            self.results.stresses = stresses
            self.results.principal_stresses = math_engine.calculate_principal_stresses(stresses)

            # ─────────────────────────────────────────────────────────────────
            # КРОК 7: ФІНІШ — надсилаємо результати у GUI
            # ─────────────────────────────────────────────────────────────────
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Завершення...", progress=100))
            wx.PostEvent(self.parent_window, CalculationDoneEvent(results=self.results))

        except Exception as e:
            self.logger.error(f"Помилка в потоці: {str(e)}", exc_info=True)
            wx.PostEvent(self.parent_window, CalculationErrorEvent(error_msg=str(e)))


class MyPanel(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(245, 245, 250))
        
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.SetScrollRate(5, 5)

        label_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        section_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        # ── Параметри сітки ──────────────────────────────────────────────────
        self.a_entry = wx.TextCtrl(self, value="2.0")
        self.b_entry = wx.TextCtrl(self, value="1.0")
        self.c_entry = wx.TextCtrl(self, value="2.0")
        self.n_A = wx.TextCtrl(self, value="2")
        self.n_B = wx.TextCtrl(self, value="1")
        self.n_C = wx.TextCtrl(self, value="2")

        # ── ZU — закріплення ─────────────────────────────────────────────────
        self.zu_entry = wx.TextCtrl(self, value="")
        self.zu_entry.SetMinSize((250, 60))

        self.zu_auto_btn = wx.Button(self, label="ZU: нижня грань (Z мін)")
        self.zu_auto_btn.Bind(wx.EVT_BUTTON, self._on_zu_auto)

        # ── ZP — навантаження ─────────────────────────────────────────────────
        self.zp_panel = ZPPanel(self)

        self.zp_auto_btn = wx.Button(self, label="ZP: верхня грань (Z макс)")
        self.zp_auto_btn.Bind(wx.EVT_BUTTON, self._on_zp_auto)

        # ── Фізичні властивості ───────────────────────────────────────────────
        self.E_entry = wx.TextCtrl(self, value="1")
        self.nu_entry = wx.TextCtrl(self, value="0.3")
        self.P_entry = wx.TextCtrl(self, value="1.0")

        for ctrl in [self.a_entry, self.b_entry, self.c_entry,
                     self.n_A, self.n_B, self.n_C,
                     self.zu_entry,
                     self.E_entry, self.nu_entry, self.P_entry]:
            ctrl.SetBackgroundColour(wx.Colour(255, 255, 255))
            ctrl.SetMinSize((150, 28))

        # ── Кнопки ─────────────────────────────────────────────────────────
        self.all_points_button = wx.Button(self, label="Розрахувати")
        self.all_points_button.Bind(wx.EVT_BUTTON, self.on_calculate)
        self.all_points_button.SetBackgroundColour(wx.Colour(52, 152, 219))
        self.all_points_button.SetMinSize((320, 40))
        calc_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.all_points_button.SetFont(calc_font)

        self.results = SimulationResults()

        self.btn_view_akt_nt = wx.Button(self, label="Переглянути AKT та NT")
        self.btn_view_dj = wx.Button(self, label="Переглянути DJ та DFIXYZ")
        self.btn_view_mge = wx.Button(self, label="Переглянути MGE")
        self.btn_view_mesh = wx.Button(self, label="Переглянути 3D сітку")
        self.btn_view_results = wx.Button(self, label="Таблиця результатів (Напруження)")
        self.btn_view_depsite_f = wx.Button(self, label="DEPSITE та Вектор сил F")
        self.btn_view_iso = wx.Button(self, label="Ізоповерхні напружень")

        for btn in [self.btn_view_akt_nt, self.btn_view_dj, self.btn_view_mge, self.btn_view_mesh,
                    self.btn_view_results, self.btn_view_depsite_f, self.btn_view_iso]:
            btn.SetBackgroundColour(wx.Colour(46, 204, 113))
            btn.SetMinSize((320, 35))
            btn.SetFont(calc_font)

        self.btn_view_akt_nt.Disable()
        self.btn_view_dj.Disable()
        self.btn_view_mge.Disable()
        self.btn_view_mesh.Disable()
        self.btn_view_results.Disable()
        self.btn_view_depsite_f.Disable()
        self.btn_view_iso.Disable()

        self.btn_view_akt_nt.Bind(wx.EVT_BUTTON, self.on_view_akt_nt)
        self.btn_view_dj.Bind(wx.EVT_BUTTON, self.on_view_dj)
        self.btn_view_mge.Bind(wx.EVT_BUTTON, self.on_view_mge)
        self.btn_view_mesh.Bind(wx.EVT_BUTTON, self.on_view_mesh)
        self.btn_view_results.Bind(wx.EVT_BUTTON, self.on_view_results)
        self.btn_view_depsite_f.Bind(wx.EVT_BUTTON, self.on_view_depsite_f)
        self.btn_view_iso.Bind(wx.EVT_BUTTON, self.on_view_iso)

        # ── Ліва колонка — параметри МСЕ ─────────────────────────────────────
        left_box = wx.StaticBoxSizer(wx.VERTICAL, self, "Параметри МСЕ")
        left_box.SetMinSize((280, -1))
        left_box_ctrl = left_box.GetStaticBox()
        left_box_ctrl.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        left_box_ctrl.SetForegroundColour(wx.Colour(52, 152, 219))

        for lbl, ctrl in [("n_x:", self.n_A), ("n_y:", self.n_B), ("n_z:", self.n_C),
                           ("A_x:", self.a_entry), ("A_y:", self.b_entry), ("A_z:", self.c_entry)]:
            st = wx.StaticText(self, label=lbl)
            st.SetFont(label_font)
            left_box.Add(st, 0, wx.ALL, 5)
            left_box.Add(ctrl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        # ── ZU — секція ───────────────────────────────────────────────────────
        zu_lbl = wx.StaticText(self, label="ZU — Закріплення (по вузлах)")
        zu_lbl.SetFont(section_font)
        left_box.Add(zu_lbl, 0, wx.ALL, 5)

        zu_hint = wx.StaticText(self, label="Номери вузлів через кому")
        zu_hint.SetFont(label_font)
        left_box.Add(zu_hint, 0, wx.LEFT | wx.RIGHT, 5)
        left_box.Add(self.zu_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        left_box.Add(self.zu_auto_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        # ── ZP — секція ───────────────────────────────────────────────────────
        zp_lbl = wx.StaticText(self, label="ZP — Навантаження (по гранях)")
        zp_lbl.SetFont(section_font)
        left_box.Add(zp_lbl, 0, wx.ALL, 5)
        left_box.Add(self.zp_panel, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        left_box.Add(self.zp_auto_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        # ── Права колонка — фізичні властивості ──────────────────────────────
        right_box = wx.StaticBoxSizer(wx.VERTICAL, self, "Фізичні властивості")
        right_box.SetMinSize((200, -1))
        right_box_ctrl = right_box.GetStaticBox()
        right_box_ctrl.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        right_box_ctrl.SetForegroundColour(wx.Colour(231, 76, 60))

        for lbl, ctrl in [("E (модуль Юнга):", self.E_entry),
                           ("ν (коефіцієнт Пуассона):", self.nu_entry),
                           ("P (сила):", self.P_entry)]:
            st = wx.StaticText(self, label=lbl)
            st.SetFont(label_font)
            right_box.Add(st, 0, wx.ALL, 5)
            right_box.Add(ctrl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        params_sizer = wx.BoxSizer(wx.HORIZONTAL)
        params_sizer.Add(left_box, 1, wx.ALL | wx.EXPAND, 10)
        params_sizer.Add(right_box, 1, wx.ALL | wx.EXPAND, 10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(params_sizer, 0, wx.ALL | wx.EXPAND, 0)

        button_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.all_points_button, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_mesh, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_akt_nt, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_dj, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_mge, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_depsite_f, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_results, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_iso, 0, wx.ALL | wx.EXPAND, 8)

        sizer.Add(button_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.status_label = wx.StaticText(self, label="Очікування розрахунку...")
        self.status_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.progress_bar = wx.Gauge(self, range=100, size=(320, 15))
        self.progress_bar.Hide()

        button_sizer.Insert(0, self.status_label, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        button_sizer.Insert(1, self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)

        self.Bind(EVT_CALCULATION_STEP, self.on_calculation_step)
        self.Bind(EVT_CALCULATION_DONE, self.on_calculation_done)
        self.Bind(EVT_CALCULATION_ERROR, self.on_calculation_error)

        self.calc_thread = None

        self.SetSizer(sizer)
        sizer.Layout()
        self.FitInside()

    # ─────────────────────────────────────────────────────────────────────────
    # ZU авто-заповнення
    # ─────────────────────────────────────────────────────────────────────────

    def _on_zu_auto(self, event):
        """Знаходить вузли на нижній грані (Z мін) і заповнює поле ZU."""
        try:
            na = int(self.n_A.GetValue().strip())
            nb = int(self.n_B.GetValue().strip())
            nc = int(self.n_C.GetValue().strip())
            a  = float(self.a_entry.GetValue().strip())
            b  = float(self.b_entry.GetValue().strip())
            c  = float(self.c_entry.GetValue().strip())
        except ValueError:
            wx.MessageBox("Введіть коректні параметри сітки (na, nb, nc, a, b, c).",
                          "Помилка", wx.OK | wx.ICON_ERROR)
            return

        mesh_gen = MeshGenerator()
        AKT = mesh_gen.separate_point(a, b, c, na, nb, nc)
        z_min = min(node[2] for node in AKT)
        zu_indices = sorted(i for i, node in enumerate(AKT) if abs(node[2] - z_min) < 1e-9)
        self.zu_entry.SetValue(', '.join(str(i) for i in zu_indices))

    def _on_zp_auto(self, event):
        """Знаходить елементи на верхній грані (Z макс) і заповнює таблицю ZP."""
        try:
            na = int(self.n_A.GetValue().strip())
            nb = int(self.n_B.GetValue().strip())
            nc = int(self.n_C.GetValue().strip())
            a  = float(self.a_entry.GetValue().strip())
            b  = float(self.b_entry.GetValue().strip())
            c  = float(self.c_entry.GetValue().strip())
        except ValueError:
            wx.MessageBox("Введіть коректні параметри сітки (na, nb, nc, a, b, c).",
                          "Помилка", wx.OK | wx.ICON_ERROR)
            return

        mesh_gen = MeshGenerator()
        AKT = mesh_gen.separate_point(a, b, c, na, nb, nc)
        elements = mesh_gen.create_points(a, b, c, na, nb, nc)
        NT = mesh_gen.NT_transform(AKT, elements)

        z_max = max(node[2] for node in AKT)
        top_elements = []
        for el_idx, node_indices in enumerate(NT):
            el_nodes = [AKT[i] for i in node_indices]
            if any(abs(node[2] - z_max) < 1e-9 for node in el_nodes):
                top_elements.append(el_idx)

        # Грань 6 = Z макс
        self.zp_panel.set_entries([(el_idx, 6) for el_idx in top_elements])

    # ─────────────────────────────────────────────────────────────────────────
    # Зчитування параметрів
    # ─────────────────────────────────────────────────────────────────────────

    def get_params_from_ui(self) -> SimulationParams:
        """Зчитує дані з GUI та пакує їх в об'єкт DTO."""
        def parse_float(ctrl, default):
            v = ctrl.GetValue().strip()
            return float(v) if v else default

        def parse_int(ctrl, default):
            v = ctrl.GetValue().strip()
            return int(v) if v else default

        self.params = SimulationParams()

        self.params.a  = parse_float(self.a_entry, self.params.a)
        self.params.b  = parse_float(self.b_entry, self.params.b)
        self.params.c  = parse_float(self.c_entry, self.params.c)
        self.params.na = parse_int(self.n_A, self.params.na)
        self.params.nb = parse_int(self.n_B, self.params.nb)
        self.params.nc = parse_int(self.n_C, self.params.nc)

        self.params.E  = parse_float(self.E_entry, self.params.E)
        self.params.nu = parse_float(self.nu_entry, self.params.nu)
        self.params.P  = parse_float(self.P_entry, self.params.P)

        if not (-1 < self.params.nu < 0.5):
            raise ValueError(
                f"Коефіцієнт Пуассона ν = {self.params.nu} виходить за фізичні межі.\n"
                "Допустимий діапазон: -1 < ν < 0.5"
            )

        # Параметри Ламе (формула 6 практикуму, заняття 1):
        #   λ = E·ν / ((1+ν)(1-2ν))  — перший параметр Ламе
        #   μ = E / (2(1+ν))          — другий параметр Ламе = модуль зсуву G
        # Використовуються у calc_MGE для побудови матриці жорсткості елемента.
        self.params.liambda = self.params.E / ((1 + self.params.nu) * (1 - 2 * self.params.nu))
        self.params.mu      = self.params.E / (2 * (1 + self.params.nu))

        # ── ZU ────────────────────────────────────────────────────────────────
        zu_raw = self.zu_entry.GetValue().strip()
        if not zu_raw:
            raise ValueError("Вкажіть номери вузлів для закріплення (ZU).\n"
                             "Скористайтесь кнопкою 'ZU: нижня грань' або введіть індекси вручну.")
        try:
            self.params.zu_node_indices = [int(x.strip()) for x in zu_raw.split(',') if x.strip()]
        except ValueError:
            raise ValueError("Індекси вузлів ZU мають бути цілими числами, наприклад: 0, 1, 2, 3")
        if not self.params.zu_node_indices:
            raise ValueError("Список вузлів ZU не може бути порожнім.")

        # ── ZP ────────────────────────────────────────────────────────────────
        self.params.zp_entries = self.zp_panel.get_entries()
        if not self.params.zp_entries:
            raise ValueError("Додайте хоча б один рядок навантаження (ZP).")

        return self.params

    def on_calculate(self, event):
        """Запускає обчислення у фоновому потоці"""
        try:
            self.params = self.get_params_from_ui()
        except ValueError as e:
            wx.MessageBox(str(e), "Помилка введення даних", wx.OK | wx.ICON_ERROR)
            return

        self.all_points_button.Disable()
        self.btn_view_dj.Disable()
        self.btn_view_mge.Disable()
        self.btn_view_mesh.Disable()
        if hasattr(self, 'btn_view_results'):
            self.btn_view_results.Disable()

        self.progress_bar.SetValue(0)
        self.progress_bar.Show()
        self.status_label.SetLabel("Підготовка до обчислень...")
        self.Layout()

        self.logger.info("Запуск фонового потоку розрахунків...")
        self.calc_thread = CalculationThread(self, self.params, self.results)
        self.calc_thread.start()

    def on_calculation_step(self, event):
        if hasattr(event, 'msg'):
            self.status_label.SetLabel(event.msg)
            self.logger.info(event.msg)

        if hasattr(event, 'progress'):
            self.progress_bar.SetValue(event.progress)

        if hasattr(event, 'enable_btn'):
            if event.enable_btn == 'mesh':
                self.btn_view_mesh.Enable()
                self.btn_view_akt_nt.Enable()
            elif event.enable_btn == 'dj':
                self.btn_view_dj.Enable()
            elif event.enable_btn == 'mge':
                self.btn_view_mge.Enable()

    def on_calculation_done(self, event):
        self.results = event.results
        self.status_label.SetLabel("Розрахунок успішно завершено!")
        self.progress_bar.Hide()
        self.all_points_button.Enable()
        self.btn_view_mesh.Enable()
        self.btn_view_akt_nt.Enable()
        self.btn_view_iso.Enable()
        if hasattr(self, 'btn_view_results'):
            self.btn_view_results.Enable()
            self.btn_view_depsite_f.Enable()
        self.Layout()
        wx.MessageBox("Розрахунок успішно завершено!\nСистему рівнянь розв'язано.", "Успіх", wx.OK | wx.ICON_INFORMATION)

    def on_calculation_error(self, event):
        self.status_label.SetLabel("Помилка розрахунку!")
        self.progress_bar.Hide()
        self.all_points_button.Enable()
        self.Layout()
        wx.MessageBox(f"Сталася помилка під час розрахунку:\n{event.error_msg}", "Помилка", wx.OK | wx.ICON_ERROR)

    def on_view_akt_nt(self, event):
        viewer = AktNtViewer(self, self.results)
        viewer.Show()

    def on_view_dj(self, event):
        viewer = GridResultsViewer(self, self.results)
        viewer.Show()

    def on_view_mge(self, event):
        viewer = MGEViewer(self, self.results.MGE)
        viewer.Show()

    def on_view_results(self, event):
        viewer = ResultsTableViewer(self, self.results)
        viewer.Show()

    def on_view_depsite_f(self, event):
        viewer = DEPSITEandFViewer(self, self.results)
        viewer.Show()

    def on_view_mesh(self, event):
        visualizer = MeshVisualizer()

        dlg = MeshScaleDialog(self)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        scale = dlg.get_scale()
        dlg.Destroy()

        if hasattr(self.results, 'displacements') and self.results.displacements is not None:
            fig = visualizer.plot_deformed_mesh(
                self.results.AKT,
                self.results.NT,
                self.results.displacements,
                self.results.stresses,
                scale_factor=scale,
                P=self.params.P,
                E=self.params.E,
            )
        else:
            fig = visualizer.plot_initial_mesh(self.results.AKT, self.results.NT,
                                               scale_factor=scale)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "statics", "result_plot.html")
        fig.write_html(output_file, auto_open=True)

    def on_view_iso(self, event):
        if self.results.stresses is None:
            wx.MessageBox("Спочатку виконайте розрахунок.", "Увага", wx.OK | wx.ICON_WARNING)
            return

        dlg = IsoSurfaceDialog(self)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        comp_key, scale = dlg.get_params()
        dlg.Destroy()

        try:
            html = build_isosurface_figure(
                self.results,
                component=comp_key,
                scale_factor=scale,
            )
        except Exception as e:
            wx.MessageBox(f"Помилка побудови ізоповерхонь:\n{e}", "Помилка", wx.OK | wx.ICON_ERROR)
            return

        script_dir  = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "statics", "isosurface.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        import webbrowser
        webbrowser.open(output_file)


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Симуляція МСЕ", size=wx.Size(750, 900))
        self.SetBackgroundColour(wx.Colour(245, 245, 250))
        self.Centre()
        panel = MyPanel(self)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
