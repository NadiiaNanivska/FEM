import wx
import wx.grid
import numpy as np


class ResultsTableViewer(wx.Frame):
    def __init__(self, parent, results):
        super().__init__(parent, title="Фінальні результати: Переміщення та Напруження", size=(1600, 720))

        self.results = results
        self.sort_col = -1
        self.sort_asc = True

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 250))
        vbox = wx.BoxSizer(wx.VERTICAL)

        self._build_summary_cards(panel, vbox)

        # -- Панель фільтрів -----------------------------------------------
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl = wx.StaticText(panel, label="Фільтр:")
        lbl.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        filter_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)

        self.filter_choice = wx.Choice(panel, choices=[
            "Всі вузли",
            "Тільки закріплені (U=0)",
            "Тільки з ненульовим переміщенням",
            "Максимальне |U| (топ 10%)",
            "Максимальне |σ| (топ 10%)",
        ])
        self.filter_choice.SetSelection(0)
        self.filter_choice.Bind(wx.EVT_CHOICE, self._on_filter)
        filter_sizer.Add(self.filter_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        self.highlight_cb = wx.CheckBox(panel, label="Підсвічування")
        self.highlight_cb.SetValue(True)
        self.highlight_cb.Bind(wx.EVT_CHECKBOX, lambda e: self.populate_grid())
        filter_sizer.Add(self.highlight_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        # Перемикач між режимами відображення
        view_lbl = wx.StaticText(panel, label="Показати:")
        filter_sizer.Add(view_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.view_choice = wx.Choice(panel, choices=[
            "Компоненти тензора (σX, σY, σZ, τXY, τYZ, τZX)",
            "Головні напруження (σ₁, σ₂, σ₃)",
            "Обидва",
        ])
        self.view_choice.SetSelection(0)
        self.view_choice.Bind(wx.EVT_CHOICE, self._on_view_change)
        filter_sizer.Add(self.view_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        export_btn = wx.Button(panel, label="Копіювати як CSV")
        export_btn.Bind(wx.EVT_BUTTON, self._on_copy_csv)
        export_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        filter_sizer.Add(export_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        vbox.Add(filter_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # -- Таблиця -------------------------------------------------------
        self.grid = wx.grid.Grid(panel)
        self._build_grid(panel)
        vbox.Add(self.grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.status_bar = wx.StaticText(panel, label="")
        self.status_bar.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.status_bar.SetForegroundColour(wx.Colour(100, 100, 100))
        vbox.Add(self.status_bar, 0, wx.LEFT | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        self._all_rows = list(range(len(self.results.AKT)))
        self.populate_grid()

    def _build_grid(self, panel):
        """Створює таблицю з потрібною кількістю стовпців."""
        num_nodes = len(self.results.AKT)
        view = self.view_choice.GetSelection()

        if hasattr(self, 'grid') and self.grid:
            self.grid.Destroy()

        self.grid = wx.grid.Grid(panel)

        if view == 0:
            cols = 12
            col_labels = ["X","Y","Z","U (x)","V (y)","W (z)",
                          "σX","σY","σZ","τXY","τYZ","τZX"]
        elif view == 1:
            cols = 9
            col_labels = ["X","Y","Z","U (x)","V (y)","W (z)",
                          "σ₁","σ₂","σ₃"]
        else:
            cols = 15
            col_labels = ["X","Y","Z","U (x)","V (y)","W (z)",
                          "σX","σY","σZ","τXY","τYZ","τZX",
                          "σ₁","σ₂","σ₃"]

        self.grid.CreateGrid(num_nodes, cols)
        self.grid.EnableEditing(False)
        self.grid.SetRowLabelSize(75)
        self.grid.SetDefaultRowSize(22)

        for i, lbl in enumerate(col_labels):
            self.grid.SetColLabelValue(i, lbl)
            self.grid.SetColSize(i, 85)

        # Arial та Segoe UI мають повну підтримку Unicode включно з ₁₂₃
        for fname in ["Segoe UI", "Arial Unicode MS", "Arial", "DejaVu Sans"]:
            f = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_BOLD, faceName=fname)
            if f.IsOk():
                self.grid.SetLabelFont(f)
                break
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self._on_col_click)

    def _on_view_change(self, event):
        """Перебудовує таблицю при зміні режиму відображення."""
        panel = self.grid.GetParent()
        sizer = panel.GetSizer()

        # Знаходимо і видаляємо стару таблицю
        for i in range(sizer.GetItemCount()):
            item = sizer.GetItem(i)
            if item and item.GetWindow() == self.grid:
                sizer.Remove(i)
                break
        self.grid.Destroy()

        self._build_grid(panel)
        # Вставляємо перед status_bar
        sizer.Insert(sizer.GetItemCount() - 1, self.grid, 1,
                     wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self._all_rows = list(range(len(self.results.AKT)))
        self.populate_grid()
        panel.Layout()

    # -- Зведені картки ----------------------------------------------------
    def _build_summary_cards(self, panel, vbox):
        if self.results.displacements is None:
            return

        disp   = self.results.displacements
        stress = self.results.stresses
        princ  = self.results.principal_stresses

        u_mag = np.sqrt(disp[::3]**2 + disp[1::3]**2 + disp[2::3]**2)

        cards = wx.BoxSizer(wx.HORIZONTAL)

        def card(label, value, color):
            p = wx.Panel(panel)
            p.SetBackgroundColour(color)
            p.SetMinSize((130, 58))
            cs = wx.BoxSizer(wx.VERTICAL)
            l = wx.StaticText(p, label=label)
            l.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            l.SetForegroundColour(wx.Colour(80, 80, 80))
            v = wx.StaticText(p, label=value)
            v.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            cs.Add(l, 0, wx.TOP | wx.LEFT, 6)
            cs.Add(v, 0, wx.LEFT | wx.BOTTOM, 6)
            p.SetSizer(cs)
            return p

        blue  = wx.Colour(232, 244, 255)
        green = wx.Colour(220, 240, 220)
        amber = wx.Colour(255, 243, 224)
        pink  = wx.Colour(255, 232, 240)
        lilac = wx.Colour(240, 232, 255)

        cards.Add(card("max |U| по X",   f"{np.abs(disp[::3]).max():.4e}",  blue),  0, wx.ALL, 4)
        cards.Add(card("max |U| по Y",   f"{np.abs(disp[1::3]).max():.4e}", blue),  0, wx.ALL, 4)
        cards.Add(card("max |U| по Z",   f"{np.abs(disp[2::3]).max():.4e}", blue),  0, wx.ALL, 4)
        cards.Add(card("max |U| (повний)", f"{u_mag.max():.4e}",              green), 0, wx.ALL, 4)

        if stress:
            s = np.array(stress)
            cards.Add(card("max |σX|",  f"{np.abs(s[:,0]).max():.4f}", amber), 0, wx.ALL, 4)
            cards.Add(card("max |σY|",  f"{np.abs(s[:,1]).max():.4f}", amber), 0, wx.ALL, 4)
            cards.Add(card("max |σZ|",  f"{np.abs(s[:,2]).max():.4f}", amber), 0, wx.ALL, 4)

        if princ:
            p = np.array(princ)
            cards.Add(card("max σ₁",  f"{p[:,0].max():.4f}", lilac), 0, wx.ALL, 4)
            cards.Add(card("max σ₂",  f"{p[:,1].max():.4f}", lilac), 0, wx.ALL, 4)
            cards.Add(card("max σ₃",  f"{p[:,2].max():.4f}", lilac), 0, wx.ALL, 4)
            cards.Add(card("min σ₁",  f"{p[:,0].min():.4f}", lilac), 0, wx.ALL, 4)
            cards.Add(card("min σ₂",  f"{p[:,1].min():.4f}", lilac), 0, wx.ALL, 4)
            cards.Add(card("min σ₃",  f"{p[:,2].min():.4f}", lilac), 0, wx.ALL, 4)

        vbox.Add(cards, 0, wx.LEFT | wx.TOP, 5)

    # -- Заповнення таблиці ------------------------------------------------
    def populate_grid(self, rows=None):
        if rows is None:
            rows = self._all_rows

        highlight = self.highlight_cb.GetValue()
        disp   = self.results.displacements
        stress = self.results.stresses
        princ  = self.results.principal_stresses
        view   = self.view_choice.GetSelection()

        if disp is not None and highlight:
            w_vals = np.array([abs(disp[3*i+2]) for i in range(len(self.results.AKT))])
            w_max  = w_vals.max() or 1.0

        if princ and highlight:
            p_arr   = np.array(princ)
            s1_max  = np.abs(p_arr[:, 0]).max() or 1.0
            s2_max  = np.abs(p_arr[:, 1]).max() or 1.0
            s3_max  = np.abs(p_arr[:, 2]).max() or 1.0

        cur = self.grid.GetNumberRows()
        if cur < len(rows):
            self.grid.AppendRows(len(rows) - cur)
        elif cur > len(rows):
            self.grid.DeleteRows(0, cur - len(rows))

        cell_font  = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        zero_color = wx.Colour(248, 248, 248)
        coord_color= wx.Colour(252, 252, 252)
        lilac_color= wx.Colour(240, 232, 255)

        self.grid.BeginBatch()
        for row_idx, node_idx in enumerate(rows):
            self.grid.SetRowLabelValue(row_idx, f"  {node_idx}")
            x, y, z = self.results.AKT[node_idx]

            for c, val in enumerate([x, y, z]):
                self.grid.SetCellValue(row_idx, c, f"{val:.3f}")
                self.grid.SetCellBackgroundColour(row_idx, c, coord_color)
                self.grid.SetCellFont(row_idx, c, cell_font)

            if disp is not None:
                u = disp[3*node_idx];  v = disp[3*node_idx+1];  w = disp[3*node_idx+2]
                for c, val in zip([3, 4, 5], [u, v, w]):
                    is_zero = abs(val) < 1e-12
                    self.grid.SetCellValue(row_idx, c, "0" if is_zero else f"{val:.5e}")
                    if highlight and not is_zero and c == 5:
                        intensity = min(int(abs(val) / w_max * 180), 180)
                        bg = wx.Colour(255 - intensity, 255, 255 - intensity // 2)
                    else:
                        bg = zero_color if is_zero else wx.WHITE
                    self.grid.SetCellBackgroundColour(row_idx, c, bg)
                    self.grid.SetCellFont(row_idx, c, cell_font)

            col_offset = 6

            # Компоненти тензора
            if view in (0, 2) and stress:
                s = stress[node_idx]
                for c_local, val in enumerate(s):
                    c = col_offset + c_local
                    is_tiny = abs(val) < 1e-6
                    self.grid.SetCellValue(row_idx, c, "0" if is_tiny else f"{val:.4f}")
                    bg = zero_color if is_tiny else wx.WHITE
                    self.grid.SetCellBackgroundColour(row_idx, c, bg)
                    self.grid.SetCellFont(row_idx, c, cell_font)
                if view == 2:
                    col_offset += 6

            # Головні напруження
            if view in (1, 2) and princ:
                p = princ[node_idx]
                s_max = [s1_max, s2_max, s3_max]
                # Кольори: σ₁ — фіолетовий, σ₂ — синьо-фіолетовий, σ₃ — блакитний
                base_colors = [
                    (220, 200, 255),  # σ₁ фіолетовий
                    (200, 215, 255),  # σ₂ синьо-фіолетовий
                    (200, 235, 255),  # σ₃ блакитний
                ]
                for c_local, val in enumerate(p):
                    c = col_offset + c_local
                    self.grid.SetCellValue(row_idx, c, f"{val:.4f}")
                    if highlight and abs(val) > 1e-6:
                        intensity = min(int(abs(val) / s_max[c_local] * 120), 120)
                        br, bg_c, bb = base_colors[c_local]
                        bg = wx.Colour(br - intensity//2, bg_c - intensity//3, bb - intensity//4)
                    else:
                        bg = wx.Colour(248, 248, 248) if abs(val) < 1e-6 else wx.WHITE
                    self.grid.SetCellBackgroundColour(row_idx, c, bg)
                    self.grid.SetCellFont(row_idx, c, cell_font)

        self.grid.EndBatch()
        self.status_bar.SetLabel(f"Показано {len(rows)} з {len(self.results.AKT)} вузлів")

    # -- Сортування --------------------------------------------------------
    def _on_col_click(self, event):
        col = event.GetCol()
        if col < 0:
            event.Skip(); return
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col; self.sort_asc = True

        disp  = self.results.displacements
        stress= self.results.stresses
        princ = self.results.principal_stresses
        view  = self.view_choice.GetSelection()

        def key_fn(ni):
            x, y, z = self.results.AKT[ni]
            if col < 3: return [x, y, z][col]
            if col < 6 and disp is not None: return disp[3*ni + (col-3)]
            if view == 0 and col < 12 and stress: return stress[ni][col-6]
            if view == 1 and col < 9 and princ: return princ[ni][col-6]
            if view == 2:
                if col < 12 and stress: return stress[ni][col-6]
                if col < 15 and princ: return princ[ni][col-12]
            return 0.0

        sorted_rows = sorted(self._all_rows, key=key_fn, reverse=not self.sort_asc)
        arrow = " ↑" if self.sort_asc else " ↓"
        for i in range(self.grid.GetNumberCols()):
            lbl = self.grid.GetColLabelValue(i).replace(" ↑","").replace(" ↓","")
            self.grid.SetColLabelValue(i, lbl + (arrow if i == col else ""))
        self.populate_grid(sorted_rows)

    # -- Фільтр ------------------------------------------------------------
    def _on_filter(self, event):
        sel  = self.filter_choice.GetSelection()
        disp = self.results.displacements
        stress = self.results.stresses
        n = len(self.results.AKT)

        if sel == 0:
            rows = list(range(n))
        elif sel == 1:
            rows = [i for i in range(n) if disp is None or (
                abs(disp[3*i]) < 1e-12 and abs(disp[3*i+1]) < 1e-12 and abs(disp[3*i+2]) < 1e-12)]
        elif sel == 2:
            rows = [i for i in range(n) if disp is not None and (
                abs(disp[3*i]) > 1e-12 or abs(disp[3*i+1]) > 1e-12 or abs(disp[3*i+2]) > 1e-12)]
        elif sel == 3 and disp is not None:
            mag = np.sqrt(disp[::3]**2 + disp[1::3]**2 + disp[2::3]**2)
            rows = [i for i in range(n) if mag[i] >= np.percentile(mag, 90)]
        elif sel == 4 and stress:
            sz = np.array([abs(s[2]) for s in stress])
            rows = [i for i in range(n) if sz[i] >= np.percentile(sz, 90)]
        else:
            rows = list(range(n))

        self._all_rows = rows
        self.populate_grid(rows)

    # -- Копіювати CSV -----------------------------------------------------
    def _on_copy_csv(self, event):
        disp  = self.results.displacements
        stress= self.results.stresses
        princ = self.results.principal_stresses
        view  = self.view_choice.GetSelection()

        if view == 0:
            header = "Вузол,X,Y,Z,U,V,W,σX,σY,σZ,τXY,τYZ,τZX"
        elif view == 1:
            header = "Вузол,X,Y,Z,U,V,W,σ1,σ2,σ3"
        else:
            header = "Вузол,X,Y,Z,U,V,W,σX,σY,σZ,τXY,τYZ,τZX,σ1,σ2,σ3"

        lines = [header]
        for i in range(len(self.results.AKT)):
            x, y, z = self.results.AKT[i]
            u = v = w = 0.0
            if disp is not None:
                u, v, w = disp[3*i], disp[3*i+1], disp[3*i+2]
            row = f"{i},{x:.4f},{y:.4f},{z:.4f},{u:.5e},{v:.5e},{w:.5e}"
            if view in (0, 2) and stress:
                row += "," + ",".join(f"{v:.5e}" for v in stress[i])
            if view in (1, 2) and princ:
                row += "," + ",".join(f"{v:.5e}" for v in princ[i])
            lines.append(row)

        text = "\n".join(lines)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox("CSV скопійовано!", "Готово", wx.OK | wx.ICON_INFORMATION)