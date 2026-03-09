import wx
import wx.grid

class MGEViewer(wx.Frame):
    def __init__(self, parent, list_of_mge):
        super().__init__(parent, title="Локальна Матриця Жорсткості Елемента (MGE 60x60)", size=(1000, 600))
        
        self.list_of_mge = list_of_mge
        self.max_elements = len(list_of_mge) - 1

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(panel, label="Виберіть номер елемента (0-based):")
        hbox.Add(lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.elem_spin = wx.SpinCtrl(panel, value='0', min=0, max=self.max_elements)
        self.elem_spin.Bind(wx.EVT_SPINCTRL, self.on_element_change)
        self.elem_spin.Bind(wx.EVT_TEXT, self.on_element_change)
        hbox.Add(self.elem_spin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)

        self.grid = wx.grid.Grid(panel)
        self.grid.CreateGrid(60, 60)
        self.grid.EnableEditing(False)
        self.grid.SetRowLabelSize(60)

        # Генеруємо підписи для осей згідно з алгоритмом calc_MGE:
        # 0-19: u1...u20 (переміщення по X)
        # 20-39: v1...v20 (переміщення по Y)
        # 40-59: w1...w20 (переміщення по Z)
        labels = []
        for i in range(1, 21): labels.append(f"u{i} (X)")
        for i in range(1, 21): labels.append(f"v{i} (Y)")
        for i in range(1, 21): labels.append(f"w{i} (Z)")

        for i in range(60):
            self.grid.SetColLabelValue(i, labels[i])
            self.grid.SetRowLabelValue(i, labels[i])

        vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(vbox)

        self.update_grid(0)

    def on_element_change(self, event):
        """Оновлює таблицю при зміні номера елемента."""
        self.update_grid(self.elem_spin.GetValue())

    def update_grid(self, elem_id):
        """Заповнює 3600 комірок таблиці даними МЖЕ."""
        mge = self.list_of_mge[elem_id]
        
        self.grid.BeginBatch()
        
        for r in range(60):
            for c in range(60):
                val = mge[r][c]

                if abs(val) < 1e-5:
                    display_val = "0.00"
                else:
                    display_val = f"{val:.4e}"
                
                self.grid.SetCellValue(r, c, display_val)
                
                if r == c:
                    self.grid.SetCellBackgroundColour(r, c, wx.Colour(230, 230, 230))
                else:
                    self.grid.SetCellBackgroundColour(r, c, wx.WHITE)

        self.grid.EndBatch()
        
        self.grid.AutoSizeColumns()