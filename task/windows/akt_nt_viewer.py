import wx
import wx.grid

from task import constants

from task.windows._ui import (
    header_panel, divider,
    BG_MAIN, CLR_ACCENT, CLR_GREEN, CLR_TEAL, CLR_AMBER,
)


class AktNtViewer(wx.Frame):

    def __init__(self, parent, results):
        nqp = len(results.AKT)
        nel = len(results.NT)
        super().__init__(
            parent,
            title=f"AKT та NT  |  вузлів: {nqp},  елементів: {nel}",
            size=(940, 700),
        )

        self.AKT = results.AKT
        self.NT  = results.NT

        panel = wx.Panel(self)
        panel.SetBackgroundColour(BG_MAIN)

        # ── Заголовок-банер ───────────────────────────────────────────────
        hdr = header_panel(
            panel,
            title="Масиви AKT та NT — сітка скінченних елементів",
            subtitle="Заняття 1, 3 (Практикум) · Формули 7 та 21",
            dims=[
                ("AKT", f"{nqp} × 3",  CLR_ACCENT),
                ("NT",  f"{nel} × 20", CLR_GREEN),
                ("nqp", str(nqp),      CLR_TEAL),
                ("nel", str(nel),      CLR_AMBER),
            ],
        )

        # ── Notebook ─────────────────────────────────────────────────────
        notebook = wx.Notebook(panel)

        akt_page = self._build_akt_page(notebook, nqp)
        nt_page  = self._build_nt_page(notebook, nel)

        notebook.AddPage(akt_page, f"AKT — координати вузлів  [{nqp} × 3]")
        notebook.AddPage(nt_page,  f"NT  — матриця зв'язності  [{nel} × 20]")

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(hdr,       0, wx.EXPAND)
        main_sizer.Add(divider(panel), 0, wx.EXPAND)
        main_sizer.Add(notebook,  1, wx.ALL | wx.EXPAND, 6)

        panel.SetSizer(main_sizer)
        self.Centre()

    # ── AKT tab ──────────────────────────────────────────────────────────────
    def _build_akt_page(self, parent, nqp):
        page = wx.Panel(parent)
        page.SetBackgroundColour(BG_MAIN)

        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(page, label="Перейти до вузла №:")
        lbl.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.akt_spin = wx.SpinCtrl(page, value='0', min=0, max=nqp - 1, size=(80, -1))
        self.akt_spin.Bind(wx.EVT_SPINCTRL, self._on_akt_goto)
        search_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        search_sizer.Add(self.akt_spin, 0, wx.ALIGN_CENTER_VERTICAL)

        grid = wx.grid.Grid(page)
        grid.CreateGrid(nqp, 3)
        grid.EnableEditing(False)
        grid.SetRowLabelSize(70)
        grid.SetDefaultRowSize(20)
        grid.SetDefaultCellFont(
            wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )

        for c, lbl_text in enumerate(["x", "y", "z"]):
            grid.SetColLabelValue(c, lbl_text)
            grid.SetColSize(c, 160)

        # Заповнюємо дані + підсвічуємо унікальні рівні z
        z_vals = sorted(set(round(row[2], 8) for row in self.AKT))
        z_colors = [
            wx.Colour(220, 235, 255),
            wx.Colour(210, 255, 210),
            wx.Colour(255, 245, 200),
            wx.Colour(255, 220, 220),
            wx.Colour(240, 215, 255),
        ]

        for r, node in enumerate(self.AKT):
            grid.SetRowLabelValue(r, str(r))
            for c, val in enumerate(node):
                grid.SetCellValue(r, c, f"{val:.6f}")
            z_idx = z_vals.index(round(node[2], 8)) % len(z_colors)
            for c in range(3):
                grid.SetCellBackgroundColour(r, c, z_colors[z_idx])

        self._akt_grid = grid

        legend_sizer = wx.BoxSizer(wx.HORIZONTAL)
        note = wx.StaticText(page, label="Колір рядка відповідає рівню z (одним кольором — один шар вузлів)")
        note.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        note.SetForegroundColour(wx.Colour(120, 120, 120))
        legend_sizer.Add(note, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(search_sizer, 0, wx.ALL, 6)
        sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        sizer.Add(legend_sizer, 0, wx.LEFT | wx.BOTTOM, 6)
        page.SetSizer(sizer)
        return page

    def _on_akt_goto(self, event):
        row = self.akt_spin.GetValue()
        if 0 <= row < self._akt_grid.GetNumberRows():
            self._akt_grid.GoToCell(row, 0)
            self._akt_grid.SelectRow(row)

    # ── NT tab ───────────────────────────────────────────────────────────────
    def _build_nt_page(self, parent, nel):
        page = wx.Panel(parent)
        page.SetBackgroundColour(BG_MAIN)

        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(page, label="Перейти до елемента №:")
        lbl.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.nt_spin = wx.SpinCtrl(page, value='0', min=0, max=nel - 1, size=(80, -1))
        self.nt_spin.Bind(wx.EVT_SPINCTRL, self._on_nt_goto)
        search_sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        search_sizer.Add(self.nt_spin, 0, wx.ALIGN_CENTER_VERTICAL)

        grid = wx.grid.Grid(page)
        grid.CreateGrid(nel, 20)
        grid.EnableEditing(False)
        grid.SetRowLabelSize(80)
        grid.SetDefaultRowSize(20)
        grid.SetDefaultCellFont(
            wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )

        # Заголовки стовпців: локальний вузол 1..20
        for c in range(constants.NODES_PER_ELEMENT):
            grid.SetColLabelValue(c, f"Лок.{c+1}")
            grid.SetColSize(c, 58)

        # Підсвітка груп вузлів у відповідності до LOCAL_NODE_COORDS_3D:
        #   0-3   (лок. 1-4)  : кутові нижньої грані → блакитний
        #   4-7   (лок. 5-8)  : кутові верхньої грані → зелений
        #   8-11  (лок. 9-12) : серединні нижньої грані → жовтий
        #   12-15 (лок. 13-16): серединні верхньої грані → помаранчевий
        #   16-19 (лок. 17-20): вертикальні серединні → ліловий
        group_colors = [
            wx.Colour(210, 230, 255),  # 1-4
            wx.Colour(200, 245, 210),  # 5-8
            wx.Colour(255, 250, 195),  # 9-12
            wx.Colour(255, 225, 195),  # 13-16
            wx.Colour(240, 215, 255),  # 17-20
        ]

        for r, el_nodes in enumerate(self.NT):
            grid.SetRowLabelValue(r, f"ел. {r}")
            for c, global_node in enumerate(el_nodes):
                grid.SetCellValue(r, c, str(global_node))
                group = c // 4
                grid.SetCellBackgroundColour(r, c, group_colors[group])

        self._nt_grid = grid

        legend_sizer = wx.BoxSizer(wx.HORIZONTAL)
        groups = [
            (group_colors[0], "лок.1-4: кутові нижньої"),
            (group_colors[1], "лок.5-8: кутові верхньої"),
            (group_colors[2], "лок.9-12: серединні нижньої"),
            (group_colors[3], "лок.13-16: серединні верхньої"),
            (group_colors[4], "лок.17-20: вертикальні"),
        ]
        for color, text in groups:
            box = wx.Panel(page, size=(12, 12))
            box.SetBackgroundColour(color)
            legend_sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 3)
            lbl2 = wx.StaticText(page, label=text)
            lbl2.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            lbl2.SetForegroundColour(wx.Colour(80, 80, 80))
            legend_sizer.Add(lbl2, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(search_sizer, 0, wx.ALL, 6)
        sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
        sizer.Add(legend_sizer, 0, wx.LEFT | wx.BOTTOM, 6)
        page.SetSizer(sizer)
        return page

    def _on_nt_goto(self, event):
        row = self.nt_spin.GetValue()
        if 0 <= row < self._nt_grid.GetNumberRows():
            self._nt_grid.GoToCell(row, 0)
            self._nt_grid.SelectRow(row)
