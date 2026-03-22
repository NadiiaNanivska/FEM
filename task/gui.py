import os
import logging
import numpy as np
import wx
from wx.lib.masked import NumCtrl
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

class CalculationThread(threading.Thread):
    def __init__(self, parent_window, params, results_obj):
        super().__init__()
        self.parent_window = parent_window
        self.params = params
        self.results = results_obj
        self.logger = logging.getLogger(__name__ + ".CalcThread")

    def run(self):
        """Метод, який виконується у фоновому потоці"""
        try:
            mesh_gen = MeshGenerator()
            math_engine = ShapeFunctionsMath()
            bc_manager = BoundaryConditionManager()

            # 1. ГЕНЕРАЦІЯ СІТКИ
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Генерація сітки...", progress=5))
            elements = mesh_gen.create_points(self.params.a, self.params.b, self.params.c, self.params.na, self.params.nb, self.params.nc)
            AKT = mesh_gen.separate_point(self.params.a, self.params.b, self.params.c, self.params.na, self.params.nb, self.params.nc)
            NT = mesh_gen.NT_transform(AKT, elements)
            AKT_RANGE = len(AKT)
            self.results.AKT = AKT
            self.results.NT = NT

            ZU = bc_manager.ZU_Chose(AKT, axis=self.params.stick_element[0], side=self.params.stick_element[1])
            self.logger.info(f"Закріплені вузли (ZU): {ZU}")

            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Сітка згенерована.", progress=10, enable_btn='mesh'))

            # 2. ОБЧИСЛЕННЯ ЯКОБІАНІВ
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

            # 3. ОБЧИСЛЕННЯ MGE
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

            # 4. ВЕКТОРИ СИЛ (FE)
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Формування векторів сил (FE)...", progress=75))
            FE = []
            gauss_weights_2d = [constants.c_1, constants.c_2, constants.c_3]
            press_axis, press_side = self.params.pressure_side

            for i in range(len(NT)):
                element_nodes = [AKT[node_idx] for node_idx in NT[i]]

                if press_side == 'min':
                    global_target = min([node[press_axis] for node in AKT])
                    el_target = min([node[press_axis] for node in element_nodes])
                else:
                    global_target = max([node[press_axis] for node in AKT])
                    el_target = max([node[press_axis] for node in element_nodes])

                if round(el_target, 6) == round(global_target, 6):
                    ZP_cast = bc_manager.ZP_Chose(element_nodes, press_axis, press_side)
                    if len(ZP_cast) == 8:
                        fe_vector = math_engine.FE_Calc(
                            gauss_weights_2d, self.params.P, ZP_cast,
                            press_axis=press_axis,
                            press_side=press_side
                        )
                        FE.append(fe_vector)
                    else:
                        FE.append(np.zeros(60).tolist())
                else:
                    FE.append(np.zeros(60).tolist())

            self.results.FE = FE

            # 5. АНСАМБЛЮВАННЯ ТА РОЗВ'ЯЗАННЯ
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Ансамблювання MGG та розв'язання рівнянь...", progress=80))

            MGG = math_engine.MG_Create(list_of_MGE, len(AKT), NT, ZU, AKT)
            F = math_engine.F_Create(FE, len(AKT), NT)

            displacements = np.linalg.solve(MGG, F)
            self.results.displacements = displacements

            # 6. НАПРУЖЕННЯ
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Обчислення напружень...", progress=95))
            stresses = math_engine.calculate_stresses(displacements, self.params.E, self.params.nu, self.results)
            self.results.stresses = stresses

            # 7. ФІНІШ
            wx.PostEvent(self.parent_window, CalculationStepEvent(msg="Завершення...", progress=100))
            wx.PostEvent(self.parent_window, CalculationDoneEvent(results=self.results))

        except Exception as e:
            self.logger.error(f"Помилка в потоці: {str(e)}", exc_info=True)
            wx.PostEvent(self.parent_window, CalculationErrorEvent(error_msg=str(e)))


class MyPanel(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(245, 245, 250))
        
        # Налаштування логування
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.SetScrollRate(5, 5)

        label_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.a_entry = wx.TextCtrl(self, value="2.0")
        self.b_entry = wx.TextCtrl(self, value="1.0")
        self.c_entry = wx.TextCtrl(self, value="2.0")

        self.n_A = wx.TextCtrl(self, value="2")
        self.n_B = wx.TextCtrl(self, value="1")
        self.n_C = wx.TextCtrl(self, value="2")

        self.stick = wx.TextCtrl(self, value="2,min")

        self.pressure_side = wx.TextCtrl(self, value="2,max")

        self.E_entry = wx.TextCtrl(self, value="1")
        self.nu_entry = wx.TextCtrl(self, value="0.3")
        self.P_entry = wx.TextCtrl(self, value="1.0")

        for ctrl in [self.a_entry, self.b_entry, self.c_entry, self.n_A, self.n_B, 
                     self.n_C, self.stick, self.pressure_side, self.E_entry, self.nu_entry, self.P_entry]:
            ctrl.SetBackgroundColour(wx.Colour(255, 255, 255))
            ctrl.SetMinSize((150, 28))

        self.all_points_button = wx.Button(self, label="Розрахувати")
        self.all_points_button.Bind(wx.EVT_BUTTON, self.on_calculate)
        self.all_points_button.SetBackgroundColour(wx.Colour(52, 152, 219))
        self.all_points_button.SetMinSize((320, 40))
        calc_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.all_points_button.SetFont(calc_font)

        self.results = SimulationResults()

        self.btn_view_dj = wx.Button(self, label="Переглянути DJ та DFIXYZ")
        self.btn_view_mge = wx.Button(self, label="Переглянути MGE")
        self.btn_view_mesh = wx.Button(self, label="Переглянути 3D сітку")
        self.btn_view_results = wx.Button(self, label="Таблиця результатів (Напруження)")
        self.btn_view_depsite_f = wx.Button(self, label="DEPSITE та Вектор сил F")

        for btn in [self.btn_view_dj, self.btn_view_mge, self.btn_view_mesh, self.btn_view_results, self.btn_view_depsite_f]:
            btn.SetBackgroundColour(wx.Colour(46, 204, 113))
            btn.SetMinSize((320, 35))
            btn.SetFont(calc_font)
        
        self.btn_view_dj.Disable()
        self.btn_view_mge.Disable()
        self.btn_view_mesh.Disable()
        self.btn_view_results.Disable()
        self.btn_view_depsite_f.Disable()

        self.btn_view_dj.Bind(wx.EVT_BUTTON, self.on_view_dj)
        self.btn_view_mge.Bind(wx.EVT_BUTTON, self.on_view_mge)
        self.btn_view_mesh.Bind(wx.EVT_BUTTON, self.on_view_mesh)
        self.btn_view_results.Bind(wx.EVT_BUTTON, self.on_view_results)
        self.btn_view_depsite_f.Bind(wx.EVT_BUTTON, self.on_view_depsite_f)

        # Ліва колонка - параметри МСЕ
        left_box = wx.StaticBoxSizer(wx.VERTICAL, self, "Параметри МСЕ")
        left_box.SetMinSize((250, -1))
        
        left_box_ctrl = left_box.GetStaticBox()
        left_box_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        left_box_ctrl.SetFont(left_box_font)
        left_box_ctrl.SetForegroundColour(wx.Colour(52, 152, 219))
        
        n_x_label = wx.StaticText(self, label="n_x:")
        n_x_label.SetFont(label_font)
        left_box.Add(n_x_label, 0, wx.ALL, 5)
        left_box.Add(self.n_A, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        n_y_label = wx.StaticText(self, label="n_y:")
        n_y_label.SetFont(label_font)
        left_box.Add(n_y_label, 0, wx.ALL, 5)
        left_box.Add(self.n_B, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        n_z_label = wx.StaticText(self, label="n_z:")
        n_z_label.SetFont(label_font)
        left_box.Add(n_z_label, 0, wx.ALL, 5)
        left_box.Add(self.n_C, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        a_x_label = wx.StaticText(self, label="A_x:")
        a_x_label.SetFont(label_font)
        left_box.Add(a_x_label, 0, wx.ALL, 5)
        left_box.Add(self.a_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        a_y_label = wx.StaticText(self, label="A_y:")
        a_y_label.SetFont(label_font)
        left_box.Add(a_y_label, 0, wx.ALL, 5)
        left_box.Add(self.b_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        a_z_label = wx.StaticText(self, label="A_z:")
        a_z_label.SetFont(label_font)
        left_box.Add(a_z_label, 0, wx.ALL, 5)
        left_box.Add(self.c_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        stick_label = wx.StaticText(self, label="Закріплена грань (0: X, 1: Y, 2: Z):")
        stick_label.SetFont(label_font)
        left_box.Add(stick_label, 0, wx.ALL, 5)
        left_box.Add(self.stick, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        pressure_label = wx.StaticText(self, label="Грань з тиском (0: X, 1: Y, 2: Z):")
        pressure_label.SetFont(label_font)
        left_box.Add(pressure_label, 0, wx.ALL, 5)
        left_box.Add(self.pressure_side, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        # Права колонка - фізичні властивості
        right_box = wx.StaticBoxSizer(wx.VERTICAL, self, "Фізичні властивості")
        right_box.SetMinSize((200, -1))
        
        right_box_ctrl = right_box.GetStaticBox()
        right_box_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        right_box_ctrl.SetFont(right_box_font)
        right_box_ctrl.SetForegroundColour(wx.Colour(231, 76, 60))
        
        e_label = wx.StaticText(self, label="E (модуль Юнга):")
        e_label.SetFont(label_font)
        right_box.Add(e_label, 0, wx.ALL, 5)
        right_box.Add(self.E_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        nu_label = wx.StaticText(self, label="ν (коефіцієнт Пуассона):")
        nu_label.SetFont(label_font)
        right_box.Add(nu_label, 0, wx.ALL, 5)
        right_box.Add(self.nu_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        p_label = wx.StaticText(self, label="P (сила):")
        p_label.SetFont(label_font)
        right_box.Add(p_label, 0, wx.ALL, 5)
        right_box.Add(self.P_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        params_sizer = wx.BoxSizer(wx.HORIZONTAL)
        params_sizer.Add(left_box, 1, wx.ALL | wx.EXPAND, 10)
        params_sizer.Add(right_box, 1, wx.ALL | wx.EXPAND, 10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(params_sizer, 0, wx.ALL | wx.EXPAND, 0)
        
        # Кнопки з кращим стилем
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.all_points_button, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_mesh, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_dj, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_mge, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_results, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_depsite_f, 0, wx.ALL | wx.EXPAND, 8)

        sizer.Add(button_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.status_label = wx.StaticText(self, label="Очікування розрахунку...")
        self.status_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.progress_bar = wx.Gauge(self, range=100, size=(320, 15))
        self.progress_bar.Hide()

        button_sizer.Insert(0, self.status_label, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        button_sizer.Insert(1, self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)

        # Прив'язуємо кастомні події
        self.Bind(EVT_CALCULATION_STEP, self.on_calculation_step)
        self.Bind(EVT_CALCULATION_DONE, self.on_calculation_done)
        self.Bind(EVT_CALCULATION_ERROR, self.on_calculation_error)

        self.calc_thread = None

        self.SetSizer(sizer)
        
        sizer.Layout()
        self.FitInside()

    def _validate_stick_element(self, value: str) -> tuple:
        """
        Валідує та розбирає формат закріпленої грані: вісь,напрям
        Повертає кортеж (вісь, напрям)
        Викидає ValueError з описом помилки
        """
        value = value.strip()
        if not value:
            raise ValueError("Закріплена грань не може бути порожною! Формат: вісь,напрям (наприклад: 0,min)")
        
        parts = [p.strip() for p in value.split(',')]
        if len(parts) != 2:
            raise ValueError("Формат закріпленої грані: вісь,напрям (наприклад: 0,min або 2,max)")
        
        axis_str, direction = parts
        
        try:
            axis = int(axis_str)
        except ValueError:
            raise ValueError("Вісь має бути числом: 0 (X), 1 (Y) або 2 (Z)")
        
        if axis not in [0, 1, 2]:
            raise ValueError("Вісь може бути тільки: 0 (X), 1 (Y), 2 (Z)")
        
        direction = direction.lower()
        if direction not in ['min', 'max']:
            raise ValueError("Напрям має бути: 'min' або 'max'")
        
        return (axis, direction)

    def get_params_from_ui(self) -> SimulationParams:
        """
        Зчитує дані з графічного інтерфейсу та пакує їх в об'єкт DTO.
        """
        def parse_float(ctrl, default):
            return float(ctrl.GetValue()) if ctrl.GetValue().strip() else default
            
        def parse_int(ctrl, default):
            return int(ctrl.GetValue()) if ctrl.GetValue().strip() else default

        self.params = SimulationParams()

        self.params.a = parse_float(self.a_entry, self.params.a)
        self.params.b = parse_float(self.b_entry, self.params.b)
        self.params.c = parse_float(self.c_entry, self.params.c)
        
        self.params.na = parse_int(self.n_A, self.params.na)
        self.params.nb = parse_int(self.n_B, self.params.nb)
        self.params.nc = parse_int(self.n_C, self.params.nc)

        self.params.E = parse_float(self.E_entry, self.params.E)
        self.params.nu = parse_float(self.nu_entry, self.params.nu)
        self.params.P = parse_float(self.P_entry, self.params.P)

        self.params.liambda = self.params.E / ((1 + self.params.nu) * (1 - 2 * self.params.nu))
        self.params.mu = self.params.E / (2 * (1 + self.params.nu))

        self.params.stick_element = self._validate_stick_element(self.stick.GetValue())

        try:
            self.params.pressure_side = self._validate_stick_element(self.pressure_side.GetValue())
        except ValueError as e:
            raise ValueError(str(e).replace("Закріплена грань", "Грань з тиском"))

        # Валідація: закріплена грань і грань з тиском не можуть бути однаковими
        if self.params.stick_element == self.params.pressure_side:
            axis_name = {0: "X", 1: "Y", 2: "Z"}[self.params.stick_element[0]]
            side_name = "мінімум" if self.params.stick_element[1] == "min" else "максимум"
            raise ValueError(
                f"Закріплена грань та грань з тиском не можуть бути однаковими!\n"
                f"Обрана грань: вісь {axis_name} ({side_name})"
            )

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
        """Обробляє проміжні повідомлення від потоку"""
        if hasattr(event, 'msg'):
            self.status_label.SetLabel(event.msg)
            self.logger.info(event.msg)

        if hasattr(event, 'progress'):
            self.progress_bar.SetValue(event.progress)

        if hasattr(event, 'enable_btn'):
            if event.enable_btn == 'mesh':
                self.btn_view_mesh.Enable()
            elif event.enable_btn == 'dj':
                self.btn_view_dj.Enable()
            elif event.enable_btn == 'mge':
                self.btn_view_mge.Enable()

    def on_calculation_done(self, event):
        """Обробляє успішне завершення розрахунків"""
        self.results = event.results

        self.status_label.SetLabel("Розрахунок успішно завершено!")
        self.progress_bar.Hide()

        self.all_points_button.Enable()
        self.btn_view_mesh.Enable()
        if hasattr(self, 'btn_view_results'):
            self.btn_view_results.Enable()
            self.btn_view_depsite_f.Enable()

        self.Layout()
        wx.MessageBox("Розрахунок успішно завершено!\nСистему рівнянь розв'язано.", "Успіх", wx.OK | wx.ICON_INFORMATION)

    def on_calculation_error(self, event):
        """Обробляє помилки, якщо потік впав"""
        self.status_label.SetLabel("Помилка розрахунку!")
        self.progress_bar.Hide()
        self.all_points_button.Enable()
        self.Layout()
        wx.MessageBox(f"Сталася помилка під час розрахунку:\n{event.error_msg}", "Помилка", wx.OK | wx.ICON_ERROR)

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

        if hasattr(self.results, 'displacements') and self.results.displacements is not None:
            scale = 1.0

            fig = visualizer.plot_deformed_mesh(
                self.results.AKT,
                self.results.NT,
                self.results.displacements,
                self.results.stresses,
                scale_factor=scale,
                P=self.params.P,
                E=self.params.E
            )
        else:
            fig = visualizer.plot_initial_mesh(self.results.AKT, self.results.NT)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "statics", "result_plot.html")
        fig.write_html(output_file, auto_open=True)


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