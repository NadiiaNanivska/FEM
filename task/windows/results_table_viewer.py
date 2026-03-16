import wx
import wx.grid

class ResultsTableViewer(wx.Frame):
    def __init__(self, parent, results):
        super().__init__(parent, title="Фінальні результати: Переміщення та Напруження", size=(1200, 600))
        
        self.results = results
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.grid = wx.grid.Grid(panel)
        num_nodes = len(self.results.AKT)
        
        self.grid.CreateGrid(num_nodes, 12)
        
        col_labels = [
            "Коорд. X", "Коорд. Y", "Коорд. Z", 
            "Переміщ. U (x)", "Переміщ. V (y)", "Переміщ. W (z)", 
            "Напруж. Sigma X", "Напруж. Sigma Y", "Напруж. Sigma Z", 
            "Дотич. Tau XY", "Дотич. Tau YZ", "Дотич. Tau ZX"
        ]
        
        for i, label in enumerate(col_labels):
            self.grid.SetColLabelValue(i, label)
            
        for i in range(num_nodes):
            self.grid.SetRowLabelValue(i, f"Вузол {i}")
            
        self.populate_grid()
        
        vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(vbox)
        
    def populate_grid(self):
        """Заповнює таблицю результатами розрахунку"""
        self.grid.BeginBatch()
        
        for i in range(len(self.results.AKT)):
            x, y, z = self.results.AKT[i]
            self.grid.SetCellValue(i, 0, f"{x:.4f}")
            self.grid.SetCellValue(i, 1, f"{y:.4f}")
            self.grid.SetCellValue(i, 2, f"{z:.4f}")
            
            if self.results.displacements is not None:
                u = self.results.displacements[i * 3 + 0]
                v = self.results.displacements[i * 3 + 1]
                w = self.results.displacements[i * 3 + 2]
                
                self.grid.SetCellValue(i, 3, "0.0000" if abs(u) < 1e-12 else f"{u:.5e}")
                self.grid.SetCellValue(i, 4, "0.0000" if abs(v) < 1e-12 else f"{v:.5e}")
                self.grid.SetCellValue(i, 5, "0.0000" if abs(w) < 1e-12 else f"{w:.5e}")
            
            if self.results.stresses is not None:
                sx, sy, sz, txy, tyz, tzx = self.results.stresses[i]
                
                self.grid.SetCellValue(i, 6, f"{sx:.4f}")
                self.grid.SetCellValue(i, 7, f"{sy:.4f}")
                self.grid.SetCellValue(i, 8, f"{sz:.4f}")
                self.grid.SetCellValue(i, 9, f"{txy:.4f}")
                self.grid.SetCellValue(i, 10, f"{tyz:.4f}")
                self.grid.SetCellValue(i, 11, f"{tzx:.4f}")
                
        self.grid.AutoSizeColumns()
        self.grid.EndBatch()