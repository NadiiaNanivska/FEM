import wx
import wx.grid
from task.fem_functions.shape_functions import ShapeFunctionsMath
from task import constants


class DEPSITEandFViewer(wx.Frame):
    """
    Вікно для перегляду матриці DEPSITE (похідні форм-функцій на грані)
    та глобального вектора сил F з двома вкладками.
    """

    def __init__(self, parent, results):
        super().__init__(
            parent,
            title="DEPSITE та Вектор сил F",
            size=(1100, 700)
        )
        self.results = results

        # Обчислюємо DEPSITE одразу
        math_engine = ShapeFunctionsMath()
        self.depsite = math_engine.DEPSITE()  # 9 точок Гауса x 8 вузлів x 2 похідні

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(panel)

        # --- Вкладка 1: DEPSITE ---
        self.tab_depsite = wx.Panel(self.notebook)
        self._build_depsite_tab()
        self.notebook.AddPage(self.tab_depsite, "DEPSITE  [9 × 8 × 2]")

        # --- Вкладка 2: F вектор ---
        self.tab_f = wx.Panel(self.notebook)
        self._build_f_tab()
        self.notebook.AddPage(self.tab_f, "Вектор сил F  [3·N]")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(main_sizer)

    # ------------------------------------------------------------------
    # Вкладка DEPSITE
    # ------------------------------------------------------------------
    def _build_depsite_tab(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Перемикач: яку похідну показувати
        choice_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(self.tab_depsite, label="Показати похідну:")
        choice_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)

        self.deriv_choice = wx.Choice(
            self.tab_depsite,
            choices=["∂ψ/∂η  (за першою координатою)", "∂ψ/∂τ  (за другою координатою)"]
        )
        self.deriv_choice.SetSelection(0)
        self.deriv_choice.Bind(wx.EVT_CHOICE, self._on_deriv_choice)
        choice_sizer.Add(self.deriv_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(choice_sizer, 0, wx.LEFT | wx.BOTTOM, 8)

        # Таблиця: 9 рядків (точки Гауса) x 8 стовпців (вузли грані)
        self.grid_depsite = wx.grid.Grid(self.tab_depsite)
        self.grid_depsite.CreateGrid(9, 8)
        self.grid_depsite.EnableEditing(False)
        self.grid_depsite.SetRowLabelSize(200)

        # Підписи стовпців
        for c in range(8):
            self.grid_depsite.SetColLabelValue(c, f"Вузол {c + 1}")

        # Підписи рядків — точки Гауса (η, τ)
        gauss_labels = []
        for eta in constants.GAUSS_POINTS:
            for tau in constants.GAUSS_POINTS:
                gauss_labels.append(f"η={eta:+.4f}, τ={tau:+.4f}")
        for r, lbl_text in enumerate(gauss_labels):
            self.grid_depsite.SetRowLabelValue(r, lbl_text)

        sizer.Add(self.grid_depsite, 1, wx.EXPAND | wx.ALL, 5)
        self.tab_depsite.SetSizer(sizer)

        self._fill_depsite_grid(deriv_idx=0)

    def _on_deriv_choice(self, event):
        self._fill_depsite_grid(self.deriv_choice.GetSelection())

    def _fill_depsite_grid(self, deriv_idx):
        """Заповнює таблицю DEPSITE для обраної похідної (0=∂η, 1=∂τ)."""
        self.grid_depsite.BeginBatch()
        for gp in range(9):
            for node in range(8):
                val = self.depsite[gp][node][deriv_idx]
                if abs(val) < 1e-14:
                    val = 0.0
                self.grid_depsite.SetCellValue(gp, node, f"{val:10.6f}")

                # Кольорове підсвічування: позитивні — синюваті, негативні — рожеві
                if val > 1e-14:
                    self.grid_depsite.SetCellBackgroundColour(gp, node, wx.Colour(220, 235, 255))
                elif val < -1e-14:
                    self.grid_depsite.SetCellBackgroundColour(gp, node, wx.Colour(255, 220, 220))
                else:
                    self.grid_depsite.SetCellBackgroundColour(gp, node, wx.WHITE)

        self.grid_depsite.EndBatch()
        self.grid_depsite.AutoSizeColumns()

    # ------------------------------------------------------------------
    # Вкладка F вектор
    # ------------------------------------------------------------------
    def _build_f_tab(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        if self.results.AKT is None or self.results.FE is None:
            sizer.Add(
                wx.StaticText(self.tab_f, label="Дані ще не розраховані. Запустіть розрахунок."),
                0, wx.ALL, 10
            )
            self.tab_f.SetSizer(sizer)
            return

        num_nodes = len(self.results.AKT)

        # Статистика
        from task.fem_functions.shape_functions import ShapeFunctionsMath
        import numpy as np
        math_engine = ShapeFunctionsMath()
        F_global = math_engine.F_Create(self.results.FE, num_nodes, self.results.NT)

        total_fx = sum(F_global[0::3])
        total_fy = sum(F_global[1::3])
        total_fz = sum(F_global[2::3])
        nonzero = sum(1 for v in F_global if abs(v) > 1e-12)

        stat_text = (
            f"Розмір вектора: {len(F_global)}   |   "
            f"Ненульових компонент: {nonzero}   |   "
            f"ΣFx={total_fx:.4f}   ΣFy={total_fy:.4f}   ΣFz={total_fz:.4f}"
        )
        stat_lbl = wx.StaticText(self.tab_f, label=stat_text)
        stat_lbl.SetForegroundColour(wx.Colour(0, 100, 0))
        font = stat_lbl.GetFont()
        font.MakeBold()
        stat_lbl.SetFont(font)
        sizer.Add(stat_lbl, 0, wx.LEFT | wx.BOTTOM, 8)

        # Фільтр — показувати тільки ненульові
        self.show_nonzero_only = wx.CheckBox(self.tab_f, label="Показати тільки ненульові рядки")
        self.show_nonzero_only.SetValue(False)
        self.show_nonzero_only.Bind(wx.EVT_CHECKBOX, lambda e: self._fill_f_grid(F_global))
        sizer.Add(self.show_nonzero_only, 0, wx.LEFT | wx.BOTTOM, 8)

        # Таблиця: num_nodes рядків x 6 стовпців (X,Y,Z координати + Fx,Fy,Fz)
        self.grid_f = wx.grid.Grid(self.tab_f)
        self.grid_f.CreateGrid(num_nodes, 6)
        self.grid_f.EnableEditing(False)
        self.grid_f.SetRowLabelSize(80)

        col_labels = ["Коорд. X", "Коорд. Y", "Коорд. Z", "Fx", "Fy", "Fz"]
        for c, lbl_text in enumerate(col_labels):
            self.grid_f.SetColLabelValue(c, lbl_text)

        # Зберігаємо F_global для використання в фільтрі
        self._F_global = F_global
        self._fill_f_grid(F_global)

        sizer.Add(self.grid_f, 1, wx.EXPAND | wx.ALL, 5)
        self.tab_f.SetSizer(sizer)

    def _fill_f_grid(self, F_global):
        """Заповнює таблицю вектора F."""
        num_nodes = len(self.results.AKT)
        show_nonzero = self.show_nonzero_only.GetValue()

        # Визначаємо які рядки показувати
        rows_to_show = []
        for i in range(num_nodes):
            fx = F_global[3 * i + 0]
            fy = F_global[3 * i + 1]
            fz = F_global[3 * i + 2]
            if show_nonzero and abs(fx) < 1e-12 and abs(fy) < 1e-12 and abs(fz) < 1e-12:
                continue
            rows_to_show.append(i)

        # Перестворюємо таблицю під потрібну кількість рядків
        current_rows = self.grid_f.GetNumberRows()
        needed = len(rows_to_show)
        if current_rows < needed:
            self.grid_f.AppendRows(needed - current_rows)
        elif current_rows > needed:
            self.grid_f.DeleteRows(0, current_rows - needed)

        self.grid_f.BeginBatch()
        for row_idx, node_idx in enumerate(rows_to_show):
            self.grid_f.SetRowLabelValue(row_idx, f"Вузол {node_idx}")

            x, y, z = self.results.AKT[node_idx]
            self.grid_f.SetCellValue(row_idx, 0, f"{x:.4f}")
            self.grid_f.SetCellValue(row_idx, 1, f"{y:.4f}")
            self.grid_f.SetCellValue(row_idx, 2, f"{z:.4f}")

            fx = F_global[3 * node_idx + 0]
            fy = F_global[3 * node_idx + 1]
            fz = F_global[3 * node_idx + 2]

            for c, val in enumerate([fx, fy, fz], start=3):
                if abs(val) < 1e-12:
                    self.grid_f.SetCellValue(row_idx, c, "0.0")
                    self.grid_f.SetCellBackgroundColour(row_idx, c, wx.WHITE)
                else:
                    self.grid_f.SetCellValue(row_idx, c, f"{val:.5e}")
                    # Підсвічуємо ненульові сили жовтим
                    self.grid_f.SetCellBackgroundColour(row_idx, c, wx.Colour(255, 250, 200))

        self.grid_f.EndBatch()
        self.grid_f.AutoSizeColumns()