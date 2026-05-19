"""
Спільні UI-компоненти для вікон програми.
"""
import wx


# ─── Палітра ──────────────────────────────────────────────────────────────────
BG_MAIN   = wx.Colour(245, 245, 250)
BG_HEADER = wx.Colour(30,  45,  80)
BG_CARD   = wx.Colour(255, 255, 255)
BG_CARD2  = wx.Colour(248, 249, 252)

CLR_ACCENT  = wx.Colour(82,  130, 255)
CLR_GREEN   = wx.Colour(46,  190, 100)
CLR_AMBER   = wx.Colour(250, 170,  40)
CLR_RED     = wx.Colour(220,  70,  70)
CLR_LILAC   = wx.Colour(150, 100, 240)
CLR_TEAL    = wx.Colour( 30, 180, 170)

TEXT_LIGHT  = wx.Colour(220, 230, 255)
TEXT_DIM    = wx.Colour(150, 160, 180)
TEXT_DARK   = wx.Colour( 40,  50,  70)


def pill(parent, text, bg=None, fg=None, bold=False):
    """
    Маленький «бейдж» з текстом і кольоровим фоном.
    Використовується для відображення розмірностей матриць.
    """
    if bg is None:
        bg = wx.Colour(70, 100, 160)
    if fg is None:
        fg = wx.Colour(255, 255, 255)

    p = wx.Panel(parent)
    p.SetBackgroundColour(bg)

    lbl = wx.StaticText(p, label=f"  {text}  ")
    lbl.SetForegroundColour(fg)
    sz = 8 if not bold else 9
    lbl.SetFont(wx.Font(sz, wx.FONTFAMILY_DEFAULT,
                        wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL,
                        faceName="Consolas"))

    s = wx.BoxSizer(wx.HORIZONTAL)
    s.Add(lbl, 0, wx.TOP | wx.BOTTOM, 3)
    p.SetSizer(s)
    return p


def header_panel(parent, title: str, subtitle: str,
                 dims: list[tuple[str, str, wx.Colour | None]]) -> wx.Panel:
    """
    Будує темний горизонтальний банер угорі вікна.

    Параметри:
        title    — назва вікна (велика)
        subtitle — підзаголовок / теоретична довідка
        dims     — список (назва_масиву, розмірність, колір_бейджа)
                   наприклад: [("MGE", "nel × 60 × 60", CLR_ACCENT), ...]
    """
    panel = wx.Panel(parent)
    panel.SetBackgroundColour(BG_HEADER)
    panel.SetMinSize((-1, 72))

    # Ліва частина: заголовок + підзаголовок
    title_lbl = wx.StaticText(panel, label=title)
    title_lbl.SetForegroundColour(wx.WHITE)
    title_lbl.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT,
                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

    sub_lbl = wx.StaticText(panel, label=subtitle)
    sub_lbl.SetForegroundColour(TEXT_DIM)
    sub_lbl.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))

    left_sizer = wx.BoxSizer(wx.VERTICAL)
    left_sizer.Add(title_lbl, 0, wx.TOP | wx.LEFT, 10)
    left_sizer.Add(sub_lbl,   0, wx.LEFT | wx.TOP, 2)

    # Права частина: бейджі розмірностей
    dim_sizer = wx.BoxSizer(wx.VERTICAL)

    dim_lbl = wx.StaticText(panel, label="РОЗМІРНОСТІ МАСИВІВ:")
    dim_lbl.SetForegroundColour(TEXT_DIM)
    dim_lbl.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT,
                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    dim_sizer.Add(dim_lbl, 0, wx.LEFT | wx.TOP, 4)

    badges_sizer = wx.BoxSizer(wx.HORIZONTAL)
    for name, dim, color in dims:
        text = f"{name}  [{dim}]"
        bg = color if color else wx.Colour(70, 100, 160)
        badges_sizer.Add(pill(panel, text, bg=bg), 0, wx.RIGHT, 5)

    dim_sizer.Add(badges_sizer, 0, wx.LEFT | wx.TOP, 4)

    main_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_sizer.Add(left_sizer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 8)
    main_sizer.AddStretchSpacer()
    main_sizer.Add(dim_sizer,  0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 8)

    panel.SetSizer(main_sizer)
    return panel


def stat_card(parent, label: str, value: str,
              bg=None, fg_val=None, width=130) -> tuple[wx.Panel, wx.StaticText]:
    """
    Картка статистики (назва + значення). Повертає (panel, value_label).
    """
    if bg is None:
        bg = BG_CARD2
    if fg_val is None:
        fg_val = TEXT_DARK

    card = wx.Panel(parent)
    card.SetBackgroundColour(bg)
    card.SetMinSize((width, 54))

    lbl_w = wx.StaticText(card, label=label)
    lbl_w.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT,
                          wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    lbl_w.SetForegroundColour(wx.Colour(110, 110, 120))

    val_w = wx.StaticText(card, label=value)
    val_w.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT,
                          wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    val_w.SetForegroundColour(fg_val)

    cs = wx.BoxSizer(wx.VERTICAL)
    cs.Add(lbl_w, 0, wx.TOP | wx.LEFT, 6)
    cs.Add(val_w, 0, wx.LEFT | wx.BOTTOM, 6)
    card.SetSizer(cs)

    return card, val_w


def divider(parent, vertical=False) -> wx.Window:
    """Тонка розділова лінія."""
    if vertical:
        line = wx.StaticLine(parent, style=wx.LI_VERTICAL)
        line.SetMinSize((1, -1))
    else:
        line = wx.StaticLine(parent, style=wx.LI_HORIZONTAL)
    line.SetBackgroundColour(wx.Colour(210, 215, 225))
    return line
