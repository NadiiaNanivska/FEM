import os
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import LinearNDInterpolator
import wx


# Словник доступних компонент
STRESS_COMPONENTS = {
    'Мізес (von Mises)':   'vm',
    'σ₁ — головне макс.':  's1',
    'σ₂ — головне сер.':   's2',
    'σ₃ — головне мін.':   's3',
    'σX':                   'sx',
    'σY':                   'sy',
    'σZ':                   'sz',
    'τXY':                  'txy',
    'τYZ':                  'tyz',
    'τZX':                  'tzx',
}


def _compute_vm(s):
    sx,sy,sz,txy,tyz,tzx = s[:,0],s[:,1],s[:,2],s[:,3],s[:,4],s[:,5]
    return np.sqrt(0.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2
                        +6*(txy**2+tyz**2+tzx**2)))


def build_isosurface_figure(results, component='vm',
                             n_iso=10, scale_factor=1.0):
    """
    Будує HTML з ізоповерхнями напружень.

    :param results:       SimulationResults
    :param component:     ключ зі STRESS_COMPONENTS.values()
    :param n_iso:         кількість ізоповерхонь
    :param scale_factor:  масштаб деформації для відображення
    :return:              HTML-рядок
    """
    AKT  = np.array(results.AKT)
    disp = np.array(results.displacements)
    s    = np.array(results.stresses)
    p    = np.array(results.principal_stresses) if results.principal_stresses else None

    n = len(AKT)

    # Деформовані координати
    ux = disp[0::3]; uy = disp[1::3]; uz = disp[2::3]
    xd = AKT[:,0] + ux * scale_factor
    yd = AKT[:,1] + uy * scale_factor
    zd = AKT[:,2] + uz * scale_factor

    # Вибираємо значення для ізоліній
    comp_map = {
        'vm':  _compute_vm(s),
        's1':  p[:,0] if p is not None else _compute_vm(s),
        's2':  p[:,1] if p is not None else s[:,1],
        's3':  p[:,2] if p is not None else s[:,2],
        'sx':  s[:,0], 'sy': s[:,1], 'sz': s[:,2],
        'txy': s[:,3], 'tyz': s[:,4], 'tzx': s[:,5],
    }
    values = comp_map.get(component, comp_map['vm'])

    # ── Інтерполяція на регулярну сітку ──────────────────────────
    nx = ny = nz = 30          # роздільна здатність сітки
    xi = np.linspace(xd.min(), xd.max(), nx)
    yi = np.linspace(yd.min(), yd.max(), ny)
    zi = np.linspace(zd.min(), zd.max(), nz)
    Xg, Yg, Zg = np.meshgrid(xi, yi, zi, indexing='ij')

    interp = LinearNDInterpolator(
        list(zip(xd, yd, zd)), values, fill_value=np.nan
    )
    Vg = interp(Xg, Yg, Zg)

    # Замінюємо NaN на мінімум (зовні тіла)
    vmin = np.nanmin(Vg)
    vmax = np.nanmax(Vg)
    Vg   = np.where(np.isnan(Vg), vmin, Vg)

    # Рівні ізоповерхонь
    iso_levels = np.linspace(vmin + (vmax-vmin)*0.05,
                             vmax - (vmax-vmin)*0.05,
                             n_iso).tolist()

    fig = go.Figure()

    # ── Ізоповерхні ──────────────────────────────────────────────
    fig.add_trace(go.Isosurface(
        x=Xg.flatten(),
        y=Yg.flatten(),
        z=Zg.flatten(),
        value=Vg.flatten(),
        isomin=vmin,
        isomax=vmax,
        surface_count=n_iso,
        colorscale='Jet',
        showscale=True,
        opacity=0.4,
        caps=dict(x_show=False, y_show=False, z_show=False),
        colorbar=dict(
            title=dict(text=component.upper(), font=dict(size=11)),
            thickness=16, len=0.6, x=1.01, tickformat='.3f',
        ),
        name='Ізоповерхні',
    ))

    # ── Каркас деформованої сітки ─────────────────────────────────
    lxd, lyd, lzd = _wireframe(xd, yd, zd, results.NT)
    fig.add_trace(go.Scatter3d(
        x=lxd, y=lyd, z=lzd,
        mode='lines', name='Сітка (деформована)',
        line=dict(color='#2c3e50', width=1),
        opacity=0.25, hoverinfo='skip',
    ))

    comp_name = next((k for k,v in STRESS_COMPONENTS.items()
                      if v == component), component)
    fig.update_layout(
        title=dict(
            text=f'Ізоповерхні: {comp_name}  |  {n_iso} рівнів  '
                 f'|  [{vmin:.4f} … {vmax:.4f}]',
            x=0.5, font=dict(size=12)
        ),
        scene=dict(
            xaxis=dict(title='X', showbackground=False),
            yaxis=dict(title='Y', showbackground=False),
            zaxis=dict(title='Z', showbackground=False),
            aspectmode='data',
            camera=dict(eye=dict(x=1.8, y=-1.8, z=1.4)),
        ),
        legend=dict(x=0.01, y=0.99,
                    bgcolor='rgba(255,255,255,0.85)',
                    font=dict(size=11)),
        margin=dict(l=0, r=80, b=20, t=60),
    )

    return fig.to_html(include_plotlyjs='cdn', full_html=True)


def _wireframe(nodes_x, nodes_y, nodes_z, nt_list):
    xl, yl, zl = [], [], []
    seen = set()
    edges = [(0,1),(1,2),(2,3),(3,0),
             (4,5),(5,6),(6,7),(7,4),
             (0,4),(1,5),(2,6),(3,7)]
    for el in nt_list:
        for a, b in edges:
            e = tuple(sorted((el[a], el[b])))
            if e not in seen:
                seen.add(e)
                xl += [nodes_x[e[0]], nodes_x[e[1]], None]
                yl += [nodes_y[e[0]], nodes_y[e[1]], None]
                zl += [nodes_z[e[0]], nodes_z[e[1]], None]
    return xl, yl, zl


# ── Діалог вибору параметрів ізоліній ────────────────────────────
class IsoSurfaceDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Параметри ізоповерхонь", size=(340, 260))

        panel = wx.Panel(self)
        vbox  = wx.BoxSizer(wx.VERTICAL)

        # Компонента напружень
        comp_lbl = wx.StaticText(panel, label="Компонента напружень:")
        vbox.Add(comp_lbl, 0, wx.ALL, 8)
        self.comp_choice = wx.Choice(panel,
                                      choices=list(STRESS_COMPONENTS.keys()))
        self.comp_choice.SetSelection(0)
        vbox.Add(self.comp_choice, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 8)

        # Кількість рівнів
        n_sizer = wx.BoxSizer(wx.HORIZONTAL)
        n_lbl = wx.StaticText(panel, label="Кількість рівнів:")
        n_sizer.Add(n_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.n_spin = wx.SpinCtrl(panel, value='10', min=3, max=30, size=(70,-1))
        n_sizer.Add(self.n_spin, 0)
        vbox.Add(n_sizer, 0, wx.ALL, 8)

        # Масштаб деформації
        sc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sc_lbl = wx.StaticText(panel, label="Масштаб деформації:")
        sc_sizer.Add(sc_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.sc_ctrl = wx.TextCtrl(panel, value="1.0", size=(70,-1))
        sc_sizer.Add(self.sc_ctrl, 0)
        vbox.Add(sc_sizer, 0, wx.LEFT | wx.RIGHT, 8)

        # Кнопки
        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn  = wx.Button(panel, wx.ID_OK, "Побудувати")
        cncl_btn= wx.Button(panel, wx.ID_CANCEL, "Скасувати")
        ok_btn.SetDefault()
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cncl_btn)
        btn_sizer.Realize()
        vbox.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 12)

        panel.SetSizer(vbox)

    def get_params(self):
        comp_name = self.comp_choice.GetStringSelection()
        comp_key  = STRESS_COMPONENTS[comp_name]
        n_iso     = self.n_spin.GetValue()
        try:
            scale = float(self.sc_ctrl.GetValue())
        except ValueError:
            scale = 1.0
        return comp_key, n_iso, scale