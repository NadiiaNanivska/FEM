import wx
import wx.grid
import numpy as np

from task import constants


class GridResultsViewer(wx.Frame):
    def __init__(self, parent, results):
        super().__init__(parent, title="DJ та DFIXYZ по елементах", size=(1050, 750))

        self.all_jacobians = results.DJ
        self.all_det_j     = results.DJ_det
        self.all_dfixyz    = results.DFIXYZ
        self.max_elements  = len(self.all_jacobians) - 1

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 250))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # -- Верхня панель керування --------------------------------------
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl_elem = wx.StaticText(panel, label="Елемент:")
        lbl_elem.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        top_sizer.Add(lbl_elem, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.elem_spin = wx.SpinCtrl(panel, value='0', min=0, max=self.max_elements, size=(70, -1))
        self.elem_spin.Bind(wx.EVT_SPINCTRL, self.on_element_change)
        self.elem_spin.Bind(wx.EVT_TEXT, self.on_element_change)
        top_sizer.Add(self.elem_spin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        top_sizer.AddSpacer(20)

        # det(J) — показуємо як бейдж з кольором
        self.lbl_det_title = wx.StaticText(panel, label="det(J):")
        self.lbl_det_title.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        top_sizer.Add(self.lbl_det_title, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.lbl_det = wx.StaticText(panel, label="[..., ...]")
        self.lbl_det.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        top_sizer.Add(self.lbl_det, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        top_sizer.AddSpacer(20)

        self.lbl_det_min_warn = wx.StaticText(panel, label="")
        self.lbl_det_min_warn.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        top_sizer.Add(self.lbl_det_min_warn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        top_sizer.AddStretchSpacer()

        # Кнопка "показати всі det(J)"
        btn_all_det = wx.Button(panel, label="Огляд det(J) по всіх елементах")
        btn_all_det.Bind(wx.EVT_BUTTON, self._on_show_all_det)
        btn_all_det.SetBackgroundColour(wx.Colour(240, 240, 240))
        top_sizer.Add(btn_all_det, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        main_sizer.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # -- Notebook з вкладками -----------------------------------------
        self.notebook = wx.Notebook(panel)

        self.grid_dj = self._create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=9,  is_dj=True)
        self.grid_dx = self._create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=constants.NODES_PER_ELEMENT)
        self.grid_dy = self._create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=constants.NODES_PER_ELEMENT)
        self.grid_dz = self._create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=constants.NODES_PER_ELEMENT)

        self.notebook.AddPage(self.grid_dj, "Якобіан DJ  [27×3×3]")
        self.notebook.AddPage(self.grid_dx, "∂φ/∂x")
        self.notebook.AddPage(self.grid_dy, "∂φ/∂y")
        self.notebook.AddPage(self.grid_dz, "∂φ/∂z")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        # -- Легенда ------------------------------------------------------
        legend_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for color, text in [
            (wx.Colour(220, 235, 255), "Позитивне"),
            (wx.Colour(255, 220, 220), "Від'ємне"),
            (wx.Colour(255, 255, 200), "Близьке до нуля"),
        ]:
            box = wx.Panel(panel, size=(14, 14))
            box.SetBackgroundColour(color)
            legend_sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
            lbl = wx.StaticText(panel, label=text)
            lbl.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            lbl.SetForegroundColour(wx.Colour(100, 100, 100))
            legend_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 14)

        main_sizer.Add(legend_sizer, 0, wx.LEFT | wx.BOTTOM, 10)

        panel.SetSizer(main_sizer)
        self.update_grids(0)

    # -- Створення таблиці ------------------------------------------------
    def _create_grid(self, parent, rows, cols, is_dj=False):
        grid = wx.grid.Grid(parent)
        grid.CreateGrid(rows, cols)
        grid.EnableEditing(False)
        grid.SetRowLabelSize(195)
        grid.SetDefaultRowSize(20)

        cell_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        grid.SetDefaultCellFont(cell_font)

        gauss_labels = []
        for a in constants.GAUSS_POINTS:
            for b in constants.GAUSS_POINTS:
                for g in constants.GAUSS_POINTS:
                    gauss_labels.append(f"α={a:+.4f} β={b:+.4f} γ={g:+.4f}")
        for r in range(rows):
            grid.SetRowLabelValue(r, gauss_labels[r])

        if is_dj:
            for c, lbl in enumerate(["J₁₁","J₁₂","J₁₃","J₂₁","J₂₂","J₂₃","J₃₁","J₃₂","J₃₃"]):
                grid.SetColLabelValue(c, lbl)
                grid.SetColSize(c, 80)
        else:
            for c in range(cols):
                grid.SetColLabelValue(c, f"φ{c+1}")
                grid.SetColSize(c, 72)

        return grid

    # -- Оновлення даних --------------------------------------------------
    def on_element_change(self, event):
        self.update_grids(self.elem_spin.GetValue())

    def update_grids(self, elem_id):
        jacobians = self.all_jacobians[elem_id]
        det_j     = self.all_det_j[elem_id]
        dfixyz    = self.all_dfixyz[elem_id]

        min_det = min(det_j)
        max_det = max(det_j)

        self.lbl_det.SetLabel(f"[{min_det:.5f},  {max_det:.5f}]")

        if min_det <= 0:
            self.lbl_det.SetForegroundColour(wx.Colour(180, 0, 0))
            self.lbl_det_min_warn.SetLabel("⚠ Від'ємний det(J)! Сітка вивернута.")
            self.lbl_det_min_warn.SetForegroundColour(wx.Colour(180, 0, 0))
        elif min_det < 0.01:
            self.lbl_det.SetForegroundColour(wx.Colour(180, 100, 0))
            self.lbl_det_min_warn.SetLabel("△ Малий det(J) — погана якість сітки")
            self.lbl_det_min_warn.SetForegroundColour(wx.Colour(180, 100, 0))
        else:
            self.lbl_det.SetForegroundColour(wx.Colour(0, 130, 0))
            self.lbl_det_min_warn.SetLabel("✓ det(J) > 0")
            self.lbl_det_min_warn.SetForegroundColour(wx.Colour(0, 130, 0))

        abs_max_det = max(abs(min_det), abs(max_det)) or 1.0

        for grid in [self.grid_dj, self.grid_dx, self.grid_dy, self.grid_dz]:
            grid.BeginBatch()

        for gp in range(constants.GAUSS_POINTS_COUNT):
            J = jacobians[gp]
            flat_J = [J[r][c] for r in range(3) for c in range(3)]
            det_val = det_j[gp]

            # Колір рядка за det(J): чим менший — тим жовтіший фон
            row_quality = min(det_val / abs_max_det, 1.0) if det_val > 0 else 0
            row_bg = wx.Colour(
                int(255 - row_quality * 15),
                int(255 - (1 - row_quality) * 60),
                int(255 - (1 - row_quality) * 60)
            )

            for c in range(9):
                val = flat_J[c]
                self._set_cell(self.grid_dj, gp, c, val, row_bg if det_val < 0.01 else None)

            for node in range(constants.NODES_PER_ELEMENT):
                dx, dy, dz = dfixyz[gp][node]
                self._set_cell(self.grid_dx, gp, node, dx)
                self._set_cell(self.grid_dy, gp, node, dy)
                self._set_cell(self.grid_dz, gp, node, dz)

        for grid in [self.grid_dj, self.grid_dx, self.grid_dy, self.grid_dz]:
            grid.EndBatch()

    def _set_cell(self, grid, row, col, val, forced_bg=None):
        """Встановлює значення і колір комірки."""
        if abs(val) < 1e-10:
            display = "0"
            bg = wx.Colour(255, 255, 200) if forced_bg is None else forced_bg
        elif val > 0:
            display = f"{val:.5f}"
            bg = wx.Colour(220, 235, 255) if forced_bg is None else forced_bg
        else:
            display = f"{val:.5f}"
            bg = wx.Colour(255, 220, 220) if forced_bg is None else forced_bg

        grid.SetCellValue(row, col, display)
        grid.SetCellBackgroundColour(row, col, bg)

    # -- Огляд det(J) по всіх елементах -----------------------------------
    def _on_show_all_det(self, event):
        dlg = wx.Dialog(self, title="det(J) по всіх елементах", size=(500, 500))
        vbox = wx.BoxSizer(wx.VERTICAL)

        grid = wx.grid.Grid(dlg)
        n = len(self.all_det_j)
        grid.CreateGrid(n, 3)
        grid.EnableEditing(False)
        grid.SetColLabelValue(0, "Елемент")
        grid.SetColLabelValue(1, "min det(J)")
        grid.SetColLabelValue(2, "max det(J)")
        grid.SetColSize(0, 80)
        grid.SetColSize(1, 160)
        grid.SetColSize(2, 160)

        for i, dets in enumerate(self.all_det_j):
            mn, mx = min(dets), max(dets)
            grid.SetCellValue(i, 0, str(i))
            grid.SetCellValue(i, 1, f"{mn:.6f}")
            grid.SetCellValue(i, 2, f"{mx:.6f}")
            if mn <= 0:
                for c in range(3):
                    grid.SetCellBackgroundColour(i, c, wx.Colour(255, 200, 200))
            elif mn < 0.01:
                for c in range(3):
                    grid.SetCellBackgroundColour(i, c, wx.Colour(255, 240, 180))

        vbox.Add(grid, 1, wx.EXPAND | wx.ALL, 8)

        close_btn = wx.Button(dlg, label="Закрити")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: dlg.Close())
        vbox.Add(close_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        dlg.SetSizer(vbox)
        dlg.ShowModal()
        dlg.Destroy()