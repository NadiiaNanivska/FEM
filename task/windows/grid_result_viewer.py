import wx
import wx.grid

from task import constants 

class GridResultsViewer(wx.Frame):
    def __init__(self, parent, results):
        super().__init__(parent, title="Лаб 4 - DJ[27] та DFIXYZ[27,20,3] для елемента", size=(1000, 600))

        self.all_jacobians = results.DJ
        self.all_det_j = results.DJ_det
        self.all_dfixyz = results.DFIXYZ
        self.max_elements = len(self.all_jacobians) - 1

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        lbl_elem = wx.StaticText(panel, label="Номер елемента (0-based):")
        top_sizer.Add(lbl_elem, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.elem_spin = wx.SpinCtrl(panel, value='0', min=0, max=self.max_elements)
        self.elem_spin.Bind(wx.EVT_SPINCTRL, self.on_element_change)
        self.elem_spin.Bind(wx.EVT_TEXT, self.on_element_change)
        top_sizer.Add(self.elem_spin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.lbl_det = wx.StaticText(panel, label="det(J) є [..., ...]")
        self.lbl_det.SetForegroundColour(wx.Colour(0, 150, 0))
        font = self.lbl_det.GetFont()
        font.MakeBold()
        self.lbl_det.SetFont(font)
        top_sizer.Add(self.lbl_det, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)

        main_sizer.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.notebook = wx.Notebook(panel)
        
        self.grid_dj = self.create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=9, is_dj=True)
        self.grid_dx = self.create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=constants.NODES_PER_ELEMENT)
        self.grid_dy = self.create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=constants.NODES_PER_ELEMENT)
        self.grid_dz = self.create_grid(self.notebook, rows=constants.GAUSS_POINTS_COUNT, cols=constants.NODES_PER_ELEMENT)

        self.notebook.AddPage(self.grid_dj, "DJ [27]")
        self.notebook.AddPage(self.grid_dx, "∂φ/∂x (DFIXYZ)")
        self.notebook.AddPage(self.grid_dy, "∂φ/∂y (DFIXYZ)")
        self.notebook.AddPage(self.grid_dz, "∂φ/∂z (DFIXYZ)")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(main_sizer)

        self.update_grids(0)

    def create_grid(self, parent, rows, cols, is_dj=False):
        """Допоміжний метод для створення та налаштування таблиці."""
        grid = wx.grid.Grid(parent)
        grid.CreateGrid(rows, cols)
        
        grid.EnableEditing(False) 
        grid.SetRowLabelSize(180) 

        gauss_roots = [-0.7746, 0.0000, 0.7746]
        gauss_labels = []
        
        for a in gauss_roots:
            for b in gauss_roots:
                for g in gauss_roots:
                    gauss_labels.append(f"({a:7.4f}, {b:7.4f}, {g:7.4f})")

        for r in range(rows):
            grid.SetRowLabelValue(r, gauss_labels[r])

        if is_dj:
            labels = ["J11", "J12", "J13", "J21", "J22", "J23", "J31", "J32", "J33"]
            for c in range(cols):
                grid.SetColLabelValue(c, labels[c])
        else:
            for c in range(cols):
                grid.SetColLabelValue(c, f"φ {c+1}")

        return grid

    def on_element_change(self, event):
        """Оновлює дані при зміні номера елемента."""
        elem_id = self.elem_spin.GetValue()
        self.update_grids(elem_id)

    def update_grids(self, elem_id):
        """Заповнює комірки таблиць масивами чисел."""
        jacobians = self.all_jacobians[elem_id]
        det_j = self.all_det_j[elem_id]
        dfixyz = self.all_dfixyz[elem_id]

        min_det, max_det = min(det_j), max(det_j)
        self.lbl_det.SetLabel(f"det(J) є [{min_det:.5f}, {max_det:.5f}]")

        self.grid_dj.BeginBatch()
        self.grid_dx.BeginBatch()
        self.grid_dy.BeginBatch()
        self.grid_dz.BeginBatch()

        for gp in range(constants.GAUSS_POINTS_COUNT):
            J = jacobians[gp]
            flat_J = [J[0][0], J[0][1], J[0][2], J[1][0], J[1][1], J[1][2], J[2][0], J[2][1], J[2][2]]
            for c in range(9):
                val = flat_J[c]
                if abs(val) < 1e-10: 
                    val = 0.0
                self.grid_dj.SetCellValue(gp, c, f"{val:.5f}")

            for node in range(constants.NODES_PER_ELEMENT):
                d_x, d_y, d_z = dfixyz[gp][node]
                
                if abs(d_x) < 1e-10: d_x = 0.0
                if abs(d_y) < 1e-10: d_y = 0.0
                if abs(d_z) < 1e-10: d_z = 0.0

                self.grid_dx.SetCellValue(gp, node, f"{d_x:.5f}")
                self.grid_dy.SetCellValue(gp, node, f"{d_y:.5f}")
                self.grid_dz.SetCellValue(gp, node, f"{d_z:.5f}")

        self.grid_dj.EndBatch()
        self.grid_dx.EndBatch()
        self.grid_dy.EndBatch()
        self.grid_dz.EndBatch()

        self.grid_dj.AutoSizeColumns()
        self.grid_dx.AutoSizeColumns()
        self.grid_dy.AutoSizeColumns()
        self.grid_dz.AutoSizeColumns()