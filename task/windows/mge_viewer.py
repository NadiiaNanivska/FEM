import wx
import wx.grid
import numpy as np


class MGEViewer(wx.Frame):
    def __init__(self, parent, list_of_mge):
        super().__init__(parent, title="Локальна Матриця Жорсткості (MGE 60×60)", size=(1100, 800))

        self.list_of_mge = list_of_mge
        self.max_elements = len(list_of_mge) - 1
        self._current_mge = None
        self._show_heatmap = True
        self._show_zeros = True

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(245, 245, 250))
        vbox = wx.BoxSizer(wx.VERTICAL)

        # -- Верхня панель ------------------------------------------------
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl = wx.StaticText(panel, label="Елемент:")
        lbl.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        top_sizer.Add(lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.elem_spin = wx.SpinCtrl(panel, value='0', min=0, max=self.max_elements, size=(70, -1))
        self.elem_spin.Bind(wx.EVT_SPINCTRL, self.on_element_change)
        self.elem_spin.Bind(wx.EVT_TEXT, self.on_element_change)
        top_sizer.Add(self.elem_spin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        top_sizer.AddSpacer(16)

        # Перемикач блоку (XX, YY, ZZ, XY, XZ, YZ)
        block_lbl = wx.StaticText(panel, label="Блок:")
        block_lbl.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        top_sizer.Add(block_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.block_choice = wx.Choice(panel, choices=[
            "Повна 60×60",
            "A₁₁ — UU (X-X)",
            "A₂₂ — VV (Y-Y)",
            "A₃₃ — WW (Z-Z)",
            "A₁₂ — UV (X-Y)",
            "A₁₃ — UW (X-Z)",
            "A₂₃ — VW (Y-Z)",
        ])
        self.block_choice.SetSelection(0)
        self.block_choice.Bind(wx.EVT_CHOICE, self._on_block_change)
        top_sizer.Add(self.block_choice, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        top_sizer.AddSpacer(16)

        self.heatmap_cb = wx.CheckBox(panel, label="Теплова карта")
        self.heatmap_cb.SetValue(True)
        self.heatmap_cb.Bind(wx.EVT_CHECKBOX, self._on_toggle_heatmap)
        top_sizer.Add(self.heatmap_cb, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.zeros_cb = wx.CheckBox(panel, label="Показати нулі")
        self.zeros_cb.SetValue(True)
        self.zeros_cb.Bind(wx.EVT_CHECKBOX, self._on_toggle_zeros)
        top_sizer.Add(self.zeros_cb, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        top_sizer.AddStretchSpacer()

        sym_btn = wx.Button(panel, label="Перевірити симетрію")
        sym_btn.Bind(wx.EVT_BUTTON, self._on_check_symmetry)
        sym_btn.SetBackgroundColour(wx.Colour(240, 240, 240))
        top_sizer.Add(sym_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        vbox.Add(top_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # -- Картки статистики --------------------------------------------
        self.stats_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._stat_panels = {}
        for key, label in [
            ("diag_min",  "min діаг."),
            ("diag_max",  "max діаг."),
            ("offdiag",   "max |позадіаг.|"),
            ("sym_err",   "несиметр. ||A-Aᵀ||"),
        ]:
            card = wx.Panel(panel)
            card.SetBackgroundColour(wx.Colour(248, 248, 248))
            card.SetMinSize((130, 54))
            cs = wx.BoxSizer(wx.VERTICAL)
            lbl_c = wx.StaticText(card, label=label)
            lbl_c.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            lbl_c.SetForegroundColour(wx.Colour(100, 100, 100))
            val_c = wx.StaticText(card, label="—")
            val_c.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            cs.Add(lbl_c, 0, wx.TOP | wx.LEFT, 6)
            cs.Add(val_c, 0, wx.LEFT | wx.BOTTOM, 6)
            card.SetSizer(cs)
            self._stat_panels[key] = val_c
            self.stats_sizer.Add(card, 0, wx.ALL, 4)

        vbox.Add(self.stats_sizer, 0, wx.LEFT | wx.RIGHT, 6)

        # -- Таблиця ------------------------------------------------------
        self.grid = wx.grid.Grid(panel)
        self.grid.CreateGrid(60, 60)
        self.grid.EnableEditing(False)
        self.grid.SetRowLabelSize(68)
        self.grid.SetColLabelSize(28)
        self.grid.SetDefaultRowSize(18)
        self.grid.SetDefaultColSize(68)

        cell_font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.grid.SetDefaultCellFont(cell_font)
        self.grid.SetDefaultCellAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)

        labels = (
            [f"u{i}(X)" for i in range(1, 21)] +
            [f"v{i}(Y)" for i in range(1, 21)] +
            [f"w{i}(Z)" for i in range(1, 21)]
        )
        for i, lbl in enumerate(labels):
            self.grid.SetColLabelValue(i, lbl)
            self.grid.SetRowLabelValue(i, lbl)

        # Групові лінії-роздільники між блоками 20×20
        self.grid.SetColSize(19, 72)
        self.grid.SetColSize(39, 72)

        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self._on_cell_select)
        vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 6)

        # -- Рядок статусу ------------------------------------------------
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cell_info = wx.StaticText(panel, label="Клікніть на комірку для деталей")
        self.cell_info.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.cell_info.SetForegroundColour(wx.Colour(100, 100, 100))
        status_sizer.Add(self.cell_info, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        copy_btn = wx.Button(panel, label="Копіювати блок як CSV")
        copy_btn.Bind(wx.EVT_BUTTON, self._on_copy_csv)
        copy_btn.SetBackgroundColour(wx.Colour(240, 240, 240))
        status_sizer.Add(copy_btn, 0, wx.ALL, 4)

        vbox.Add(status_sizer, 0, wx.EXPAND)

        # -- Легенда ------------------------------------------------------
        leg_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for color, text in [
            (wx.Colour(180, 210, 255), "Великі позитивні"),
            (wx.Colour(220, 235, 255), "Малі позитивні"),
            (wx.Colour(255, 240, 200), "Нулі / малі"),
            (wx.Colour(255, 210, 210), "Малі від'ємні"),
            (wx.Colour(255, 160, 160), "Великі від'ємні"),
            (wx.Colour(200, 230, 200), "Діагональ"),
        ]:
            box = wx.Panel(panel, size=(12, 12))
            box.SetBackgroundColour(color)
            leg_sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 3)
            l = wx.StaticText(panel, label=text)
            l.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            l.SetForegroundColour(wx.Colour(100, 100, 100))
            leg_sizer.Add(l, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        vbox.Add(leg_sizer, 0, wx.LEFT | wx.BOTTOM, 8)

        panel.SetSizer(vbox)
        self.update_grid(0)

    # -- Оновлення --------------------------------------------------------
    def on_element_change(self, event):
        self.update_grid(self.elem_spin.GetValue())

    def _on_block_change(self, event):
        self.update_grid(self.elem_spin.GetValue())

    def _on_toggle_heatmap(self, event):
        self._show_heatmap = self.heatmap_cb.GetValue()
        self.update_grid(self.elem_spin.GetValue())

    def _on_toggle_zeros(self, event):
        self._show_zeros = self.zeros_cb.GetValue()
        self.update_grid(self.elem_spin.GetValue())

    def update_grid(self, elem_id):
        mge = np.array(self.list_of_mge[elem_id])
        self._current_mge = mge

        # -- Статистика ---------------------------------------------------
        diag = np.diag(mge)
        off  = mge - np.diag(diag)
        sym_err = np.linalg.norm(mge - mge.T)

        self._stat_panels["diag_min"].SetLabel(f"{diag.min():.4f}")
        self._stat_panels["diag_max"].SetLabel(f"{diag.max():.4f}")
        self._stat_panels["offdiag"].SetLabel(f"{np.abs(off).max():.4f}")

        if sym_err < 1e-8:
            self._stat_panels["sym_err"].SetLabel("0  ✓")
            self._stat_panels["sym_err"].SetForegroundColour(wx.Colour(0, 130, 0))
        else:
            self._stat_panels["sym_err"].SetLabel(f"{sym_err:.3e}")
            self._stat_panels["sym_err"].SetForegroundColour(wx.Colour(180, 80, 0))

        # -- Визначення підматриці ----------------------------------------
        block = self.block_choice.GetSelection()
        if block == 0:
            sub = mge
            r0, c0, size = 0, 0, 60
        else:
            # блоки 20×20: (r0,c0) по вибору
            offsets = [(0,0),(20,20),(40,40),(0,20),(0,40),(20,40)]
            r0, c0 = offsets[block - 1]
            size = 20
            sub = mge[r0:r0+size, c0:c0+size]

        # Перестворюємо таблицю якщо розмір змінився
        cur_rows = self.grid.GetNumberRows()
        cur_cols = self.grid.GetNumberCols()
        if cur_rows != size:
            if cur_rows < size:
                self.grid.AppendRows(size - cur_rows)
                self.grid.AppendCols(size - cur_cols)
            else:
                self.grid.DeleteRows(0, cur_rows - size)
                self.grid.DeleteCols(0, cur_cols - size)

        labels_all = (
            [f"u{i}(X)" for i in range(1, 21)] +
            [f"v{i}(Y)" for i in range(1, 21)] +
            [f"w{i}(Z)" for i in range(1, 21)]
        )
        for i in range(size):
            self.grid.SetColLabelValue(i, labels_all[c0 + i])
            self.grid.SetRowLabelValue(i, labels_all[r0 + i])
            self.grid.SetColSize(i, 68)

        # -- Теплова карта ------------------------------------------------
        abs_max = np.abs(sub).max() or 1.0

        self.grid.BeginBatch()
        for r in range(size):
            for c in range(size):
                val = sub[r, c]
                is_zero = abs(val) < 1e-5

                # Текст
                if is_zero and not self._show_zeros:
                    display = ""
                elif is_zero:
                    display = "0"
                elif abs(val) >= 1000:
                    display = f"{val:.2e}"
                elif abs(val) >= 0.01:
                    display = f"{val:.4f}"
                else:
                    display = f"{val:.3e}"

                self.grid.SetCellValue(r, c, display)

                # Колір
                is_diag = (r == c) and (block == 0 or r0 == c0)
                if is_diag:
                    bg = wx.Colour(200, 230, 200)
                elif self._show_heatmap and not is_zero:
                    ratio = abs(val) / abs_max
                    if val > 0:
                        intensity = int(ratio * 160)
                        bg = wx.Colour(220 - intensity, 235 - intensity // 2, 255)
                    else:
                        intensity = int(ratio * 160)
                        bg = wx.Colour(255, 235 - intensity // 2, 235 - intensity)
                elif is_zero:
                    bg = wx.Colour(255, 250, 220)
                else:
                    bg = wx.WHITE

                self.grid.SetCellBackgroundColour(r, c, bg)

        self.grid.EndBatch()

    # -- Деталі комірки ---------------------------------------------------
    def _on_cell_select(self, event):
        r, c = event.GetRow(), event.GetCol()
        if self._current_mge is None:
            event.Skip()
            return
        block = self.block_choice.GetSelection()
        offsets = [(0,0),(0,0),(20,20),(40,40),(0,20),(0,40),(20,40)]
        r0, c0 = offsets[block]
        gr, gc = r0 + r, c0 + c
        val = self._current_mge[gr, gc]
        sym_val = self._current_mge[gc, gr]
        sym_diff = abs(val - sym_val)

        labels = (
            [f"u{i}(X)" for i in range(1, 21)] +
            [f"v{i}(Y)" for i in range(1, 21)] +
            [f"w{i}(Z)" for i in range(1, 21)]
        )
        row_lbl = labels[gr]
        col_lbl = labels[gc]

        info = f"[{gr},{gc}]  {row_lbl} × {col_lbl}  =  {val:.6f}"
        if gr != gc:
            info += f"   |   транспонована [{gc},{gr}] = {sym_val:.6f}   |   різниця = {sym_diff:.2e}"
        self.cell_info.SetLabel(info)
        event.Skip()

    # -- Перевірка симетрії -----------------------------------------------
    def _on_check_symmetry(self, event):
        if self._current_mge is None:
            return
        mge = self._current_mge
        diff = np.abs(mge - mge.T)
        max_diff = diff.max()
        idx = np.unravel_index(diff.argmax(), diff.shape)

        labels = (
            [f"u{i}(X)" for i in range(1, 21)] +
            [f"v{i}(Y)" for i in range(1, 21)] +
            [f"w{i}(Z)" for i in range(1, 21)]
        )

        if max_diff < 1e-8:
            msg = "✓ Матриця симетрична (||A - Aᵀ||_max < 1e-8)"
            style = wx.ICON_INFORMATION
        else:
            r, c = idx
            msg = (
                f"Матриця НЕ симетрична!\n\n"
                f"||A - Aᵀ||_max = {max_diff:.4e}\n"
                f"Найбільша різниця у позиції [{r}, {c}]:\n"
                f"  A[{r},{c}] = {mge[r,c]:.6f}  ({labels[r]} × {labels[c]})\n"
                f"  A[{c},{r}] = {mge[c,r]:.6f}  ({labels[c]} × {labels[r]})\n"
            )
            style = wx.ICON_WARNING

        wx.MessageBox(msg, "Перевірка симетрії MGE", wx.OK | style)

    # -- Копіювати CSV ----------------------------------------------------
    def _on_copy_csv(self, event):
        if self._current_mge is None:
            return
        block = self.block_choice.GetSelection()
        offsets = [(0,0),(0,0),(20,20),(40,40),(0,20),(0,40),(20,40)]
        sizes   = [60,20,20,20,20,20,20]
        r0, c0  = offsets[block]
        size    = sizes[block]
        sub = self._current_mge[r0:r0+size, c0:c0+size]

        lines = [",".join([f"{v:.6e}" for v in row]) for row in sub]
        text = "\n".join(lines)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox(f"Скопійовано блок {size}×{size} як CSV!", "Готово", wx.OK | wx.ICON_INFORMATION)