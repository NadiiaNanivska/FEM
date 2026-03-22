import wx
import wx.grid
import numpy as np


class ResultsTableViewer(wx.Frame):
    def __init__(self, parent, results):
        super().__init__(parent, title="Фінальні результати: Переміщення та Напруження", size=(1500, 720))

        self.results = results
        self.sort_col = -1
        self.sort_asc = True

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 250))
        vbox = wx.BoxSizer(wx.VERTICAL)

        # ── Зведені картки ──────────────────────────────────────────────
        self._build_summary_cards(panel, vbox)

        # ── Панель фільтрів ──────────────────────────────────────────────
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)

        filter_lbl = wx.StaticText(panel, label="Фільтр вузлів:")
        filter_lbl.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        filter_sizer.Add(filter_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)

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

        self.highlight_cb = wx.CheckBox(panel, label="Підсвічування значень")
        self.highlight_cb.SetValue(True)
        self.highlight_cb.Bind(wx.EVT_CHECKBOX, lambda e: self.populate_grid())
        filter_sizer.Add(self.highlight_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        export_btn = wx.Button(panel, label="Копіювати як CSV")
        export_btn.Bind(wx.EVT_BUTTON, self._on_copy_csv)
        export_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        filter_sizer.Add(export_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        vbox.Add(filter_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # ── Таблиця ──────────────────────────────────────────────────────
        num_nodes = len(self.results.AKT)
        self.grid = wx.grid.Grid(panel)
        self.grid.CreateGrid(num_nodes, 12)
        self.grid.EnableEditing(False)
        self.grid.SetRowLabelSize(75)
        self.grid.SetDefaultRowSize(22)

        col_labels = [
            "X", "Y", "Z",
            "U (x)", "V (y)", "W (z)",
            "σX", "σY", "σZ",
            "τXY", "τYZ", "τZX"
        ]
        col_widths = [65, 65, 65, 95, 95, 95, 80, 80, 80, 75, 75, 75]

        header_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        for i, (label, w) in enumerate(zip(col_labels, col_widths)):
            self.grid.SetColLabelValue(i, label)
            self.grid.SetColSize(i, w)

        self.grid.SetLabelFont(header_font)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self._on_col_click)

        # Групові кольори заголовків (через малювання не можна, але підказуємо через назви)
        vbox.Add(self.grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # ── Рядок статусу ────────────────────────────────────────────────
        self.status_bar = wx.StaticText(panel, label="")
        self.status_bar.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.status_bar.SetForegroundColour(wx.Colour(100, 100, 100))
        vbox.Add(self.status_bar, 0, wx.LEFT | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        self._all_rows = list(range(num_nodes))
        self.populate_grid()

    # ── Зведені картки ───────────────────────────────────────────────────
    def _build_summary_cards(self, panel, vbox):
        if self.results.displacements is None:
            return

        disp = self.results.displacements
        stress = self.results.stresses

        u_vals = [abs(disp[3*i])   for i in range(len(self.results.AKT))]
        v_vals = [abs(disp[3*i+1]) for i in range(len(self.results.AKT))]
        w_vals = [abs(disp[3*i+2]) for i in range(len(self.results.AKT))]

        max_u = max(u_vals)
        max_v = max(v_vals)
        max_w = max(w_vals)
        max_total = max(np.sqrt(disp[::3]**2 + disp[1::3]**2 + disp[2::3]**2))

        cards_sizer = wx.BoxSizer(wx.HORIZONTAL)

        def make_card(label, value, color):
            card = wx.Panel(panel)
            card.SetBackgroundColour(color)
            card.SetMinSize((140, 60))
            cs = wx.BoxSizer(wx.VERTICAL)
            lbl = wx.StaticText(card, label=label)
            lbl.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            lbl.SetForegroundColour(wx.Colour(80, 80, 80))
            val = wx.StaticText(card, label=value)
            val.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            cs.Add(lbl, 0, wx.TOP | wx.LEFT, 8)
            cs.Add(val, 0, wx.LEFT | wx.BOTTOM, 8)
            card.SetSizer(cs)
            return card

        blue  = wx.Colour(232, 244, 255)
        green = wx.Colour(220, 240, 220)
        amber = wx.Colour(255, 243, 224)
        pink  = wx.Colour(255, 232, 240)

        # Переміщення
        cards_sizer.Add(make_card("max |U| по X",    f"{max_u:.4e}",     blue),  0, wx.ALL, 4)
        cards_sizer.Add(make_card("max |V| по Y",    f"{max_v:.4e}",     blue),  0, wx.ALL, 4)
        cards_sizer.Add(make_card("max |W| по Z",    f"{max_w:.4e}",     blue),  0, wx.ALL, 4)
        cards_sizer.Add(make_card("max |U| повний",  f"{max_total:.4e}", green), 0, wx.ALL, 4)

        if stress:
            # Нормальні напруження — індекси 0,1,2
            sx_vals  = [abs(s[0]) for s in stress]
            sy_vals  = [abs(s[1]) for s in stress]
            sz_vals  = [abs(s[2]) for s in stress]

            cards_sizer.Add(make_card("max |σX|",  f"{max(sx_vals):.4f}",  amber), 0, wx.ALL, 4)
            cards_sizer.Add(make_card("max |σY|",  f"{max(sy_vals):.4f}",  amber), 0, wx.ALL, 4)
            cards_sizer.Add(make_card("max |σZ|",  f"{max(sz_vals):.4f}",  amber), 0, wx.ALL, 4)

        vbox.Add(cards_sizer, 0, wx.LEFT | wx.TOP, 5)

    # ── Заповнення таблиці ───────────────────────────────────────────────
    def populate_grid(self, rows=None):
        if rows is None:
            rows = self._all_rows

        highlight = self.highlight_cb.GetValue()
        disp = self.results.displacements
        stress = self.results.stresses

        # Нормалізатори для теплових карт
        if disp is not None and highlight:
            w_vals = np.array([abs(disp[3*i+2]) for i in range(len(self.results.AKT))])
            w_max = w_vals.max() or 1.0
        if stress and highlight:
            sz_vals = np.array([abs(s[2]) for s in stress])
            sz_max = sz_vals.max() or 1.0

        # Перестворюємо рядки якщо треба
        cur = self.grid.GetNumberRows()
        needed = len(rows)
        if cur < needed:
            self.grid.AppendRows(needed - cur)
        elif cur > needed:
            self.grid.DeleteRows(0, cur - needed)

        self.grid.BeginBatch()

        cell_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        zero_color  = wx.Colour(248, 248, 248)
        coord_color = wx.Colour(252, 252, 252)

        for row_idx, node_idx in enumerate(rows):
            self.grid.SetRowLabelValue(row_idx, f"  {node_idx}")
            x, y, z = self.results.AKT[node_idx]

            # Координати — сірий фон
            for c, val in enumerate([x, y, z]):
                self.grid.SetCellValue(row_idx, c, f"{val:.3f}")
                self.grid.SetCellBackgroundColour(row_idx, c, coord_color)
                self.grid.SetCellFont(row_idx, c, cell_font)

            # Переміщення
            if disp is not None:
                u = disp[3*node_idx];  v = disp[3*node_idx+1];  w = disp[3*node_idx+2]
                for c, val in zip([3, 4, 5], [u, v, w]):
                    is_zero = abs(val) < 1e-12
                    self.grid.SetCellValue(row_idx, c, "0" if is_zero else f"{val:.5e}")
                    if highlight and not is_zero:
                        # Теплова карта по W (переміщення по Z)
                        intensity = min(int(abs(val) / w_max * 180), 180) if c == 5 else 0
                        self.grid.SetCellBackgroundColour(row_idx, c, wx.Colour(255 - intensity, 255, 255 - intensity // 2))
                    else:
                        self.grid.SetCellBackgroundColour(row_idx, c, zero_color if is_zero else wx.WHITE)
                    self.grid.SetCellFont(row_idx, c, cell_font)

            # Напруження
            if stress:
                s = stress[node_idx]
                for c, val in zip(range(6, 12), s):
                    is_tiny = abs(val) < 1e-6
                    self.grid.SetCellValue(row_idx, c, "0" if is_tiny else f"{val:.4f}")
                    if highlight and not is_tiny and c == 8:  # σZ — теплова карта
                        intensity = min(int(abs(val) / sz_max * 160), 160)
                        bg = wx.Colour(255, 255 - intensity // 2, 255 - intensity)
                        self.grid.SetCellBackgroundColour(row_idx, c, bg)
                    elif is_tiny:
                        self.grid.SetCellBackgroundColour(row_idx, c, zero_color)
                    else:
                        self.grid.SetCellBackgroundColour(row_idx, c, wx.WHITE)
                    self.grid.SetCellFont(row_idx, c, cell_font)

        self.grid.EndBatch()
        self.status_bar.SetLabel(f"Показано {len(rows)} з {len(self.results.AKT)} вузлів")

    # ── Сортування по стовпцю ────────────────────────────────────────────
    def _on_col_click(self, event):
        col = event.GetCol()
        if col < 0:
            event.Skip()
            return
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col
            self.sort_asc = True

        disp = self.results.displacements
        stress = self.results.stresses

        def key_fn(node_idx):
            x, y, z = self.results.AKT[node_idx]
            coords = [x, y, z]
            if col < 3:
                return coords[col]
            if col < 6 and disp is not None:
                return disp[3*node_idx + (col - 3)]
            if col < 12 and stress:
                return stress[node_idx][col - 6]
            return 0.0

        sorted_rows = sorted(self._all_rows, key=key_fn, reverse=not self.sort_asc)
        arrow = " ↑" if self.sort_asc else " ↓"
        col_labels = ["X","Y","Z","U (x)","V (y)","W (z)","σX","σY","σZ","τXY","τYZ","τZX"]
        for i, lbl in enumerate(col_labels):
            suffix = arrow if i == col else ""
            self.grid.SetColLabelValue(i, lbl + suffix)

        self.populate_grid(sorted_rows)

    # ── Фільтр ───────────────────────────────────────────────────────────
    def _on_filter(self, event):
        sel = self.filter_choice.GetSelection()
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
            magnitudes = np.sqrt(disp[::3]**2 + disp[1::3]**2 + disp[2::3]**2)
            threshold = np.percentile(magnitudes, 90)
            rows = [i for i in range(n) if magnitudes[i] >= threshold]
        elif sel == 4 and stress:
            sz_vals = np.array([abs(s[2]) for s in stress])
            threshold = np.percentile(sz_vals, 90)
            rows = [i for i in range(n) if sz_vals[i] >= threshold]
        else:
            rows = list(range(n))

        self._all_rows = rows
        self.populate_grid(rows)

    # ── Копіювати CSV ────────────────────────────────────────────────────
    def _on_copy_csv(self, event):
        lines = ["Вузол,X,Y,Z,U,V,W,σX,σY,σZ,τXY,τYZ,τZX"]
        disp = self.results.displacements
        stress = self.results.stresses
        for i in range(len(self.results.AKT)):
            x, y, z = self.results.AKT[i]
            u = v = w = 0.0
            if disp is not None:
                u, v, w = disp[3*i], disp[3*i+1], disp[3*i+2]
            sx = sy = sz = txy = tyz = tzx = 0.0
            if stress:
                sx, sy, sz, txy, tyz, tzx = stress[i]
            lines.append(f"{i},{x:.4f},{y:.4f},{z:.4f},{u:.5e},{v:.5e},{w:.5e},"
                         f"{sx:.5e},{sy:.5e},{sz:.5e},{txy:.5e},{tyz:.5e},{tzx:.5e}")
        text = "\n".join(lines)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox("CSV скопійовано в буфер обміну!", "Готово", wx.OK | wx.ICON_INFORMATION)