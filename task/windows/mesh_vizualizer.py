import numpy as np
import plotly.graph_objects as go


class MeshVisualizer:
    def __init__(self):
        pass

    def plot_initial_mesh(self, global_nodes, nt_list):
        x = [n[0] for n in global_nodes]
        y = [n[1] for n in global_nodes]
        z = [n[2] for n in global_nodes]
        n = len(x)

        fig = go.Figure()

        lx, ly, lz = self._wireframe(x, y, z, nt_list)
        fig.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz, mode='lines', name='Сітка',
            line=dict(color='#2980b9', width=1), hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z, mode='markers+text', name='Вузли',
            marker=dict(size=3, color='#e74c3c'),
            text=[str(i) for i in range(n)],
            textposition='top center', textfont=dict(size=8),
            hovertemplate='Вузол %{text}<br>X=%{x:.3f} Y=%{y:.3f} Z=%{z:.3f}<extra></extra>',
        ))
        fig.update_layout(**self._base_layout(
            f'Початкова сітка — {len(nt_list)} елементів, {n} вузлів'
        ))
        return fig

#     def plot_deformed_mesh(self, global_nodes, nt_list, displacements,
#                            stresses, scale_factor=1.0, P=0, E=0):
#         n = len(global_nodes)
#         x0 = np.array([nd[0] for nd in global_nodes])
#         y0 = np.array([nd[1] for nd in global_nodes])
#         z0 = np.array([nd[2] for nd in global_nodes])
#
#         U   = np.array(displacements)
#         ux  = U[0::3]; uy = U[1::3]; uz = U[2::3]
#
#         s   = np.array(stresses) if stresses else np.zeros((n, 6))
#         sx  = s[:, 0]; sy = s[:, 1]; sz = s[:, 2]
#         txy = s[:, 3]; tyz = s[:, 4]; tzx = s[:, 5]
#         vm  = np.sqrt(0.5 * ((sx-sy)**2 + (sy-sz)**2 + (sz-sx)**2
#                              + 6*(txy**2 + tyz**2 + tzx**2)))
#
#         xd = x0 + ux * scale_factor
#         yd = y0 + uy * scale_factor
#         zd = z0 + uz * scale_factor
#
#         # Wireframe
#         lx0, ly0, lz0 = self._wireframe(x0.tolist(), y0.tolist(), z0.tolist(), nt_list)
#         lxd, lyd, lzd = self._wireframe(xd.tolist(), yd.tolist(), zd.tolist(), nt_list)
#
#         # Hover тексти для деформованих вузлів
#         hover = []
#         for i in range(n):
#             hover.append(
#                 f'<b>Вузол {i}</b><br>'
#                 f'────────────────<br>'
#                 f'<b>Нові координати:</b><br>'
#                 f'X = {xd[i]:.5f}<br>'
#                 f'Y = {yd[i]:.5f}<br>'
#                 f'Z = {zd[i]:.5f}<br>'
#                 f'────────────────<br>'
#                 f'<b>Переміщення:</b><br>'
#                 f'U = {ux[i]:.4e}<br>'
#                 f'V = {uy[i]:.4e}<br>'
#                 f'W = {uz[i]:.4e}<br>'
#                 f'────────────────<br>'
#                 f'<b>Напруження:</b><br>'
#                 f'σX = {sx[i]:.4f}<br>'
#                 f'σY = {sy[i]:.4f}<br>'
#                 f'σZ = {sz[i]:.4f}<br>'
#                 f'τXY = {txy[i]:.4f}<br>'
#                 f'τYZ = {tyz[i]:.4f}<br>'
#                 f'τZX = {tzx[i]:.4f}<br>'
#                 f'────────────────<br>'
#             )
#
#         fig = go.Figure()
#
#         fig.add_trace(go.Scatter3d(
#             x=lx0, y=ly0, z=lz0,
#             mode='lines', name='До деформації',
#             line=dict(color='#FF0000', width=2),
#             opacity=0.35, hoverinfo='skip',
#         ))
#
#         fig.add_trace(go.Scatter3d(
#             x=lxd, y=lyd, z=lzd,
#             mode='lines', name='Після деформації',
#             line=dict(color='#2ecc71', width=2),
#             hoverinfo='skip',
#         ))
#
#         fig.add_trace(go.Scatter3d(
#             x=x0, y=y0, z=z0,
#             mode='markers', name='Початкові вузли',
#             marker=dict(size=3, color='#7f8c8d', opacity=0.5),
#             hoverinfo='skip',
#         ))
#
#         # trace 3 — початкові вузли З номерами (приховані за замовч.)
#         fig.add_trace(go.Scatter3d(
#             x=x0, y=y0, z=z0,
#             mode='markers+text', name='Номери вузлів',
#             marker=dict(size=3, color='#7f8c8d', opacity=0.5),
#             text=[str(i) for i in range(n)],
#             textposition='top center',
#             textfont=dict(size=8, color='#2c3e50'),
#             hoverinfo='skip',
#             visible=True,
#         ))
#
#         # trace 4 — деформовані вузли
#         fig.add_trace(go.Scatter3d(
#             x=xd, y=yd, z=zd,
#             mode='markers',
#             marker=dict(size=3, color='#154a23', opacity=0.7),
#             name='Деформовані вузли',
#             text=hover,
#             hovertemplate='%{text}<extra></extra>',
#         ))
#
#         # Кнопка нумерації через Plotly updatemenus
#         fig.update_layout(
#             updatemenus=[dict(
#                 type='buttons',
#                 direction='left',
#                 x=0.0, xanchor='left',
#                 y=1.08, yanchor='top',
#                 showactive=True,
#                 buttons=[
#                     dict(
#                         label='Номери вузлів: увімк.',
#                         method='update',
#                         args=[{'visible': [True, True, False, True, True]}],
#                     ),
#                     dict(
#                         label='Номери вузлів: вимк.',
#                         method='update',
#                         args=[{'visible': [True, True, True, False, True]}],
#                     ),
#                 ],
#                 bgcolor='#ecf0f1',
#                 bordercolor='#bdc3c7',
#                 font=dict(size=11),
#             )]
#         )
#
#         title = (
#             f'Деформація паралелепіпеда  |  '
#             f'E = {E}  |  '
#             f'P = {P}  |  '
#             f'масштаб ×{scale_factor}  |  '
#             f'{len(nt_list)} елементів, {n} вузлів'
#         )
#
#         layout = self._base_layout(title)
#         layout['margin'] = dict(l=0, r=90, b=40, t=100)
#         fig.update_layout(**layout)
#
#         return fig

    def plot_deformed_mesh(self, global_nodes, nt_list, displacements,
                               stresses, scale_factor=1.0, P=0, E=0):
            n = len(global_nodes)
            x0 = np.array([nd[0] for nd in global_nodes])
            y0 = np.array([nd[1] for nd in global_nodes])
            z0 = np.array([nd[2] for nd in global_nodes])

            U   = np.array(displacements)
            ux  = U[0::3]; uy = U[1::3]; uz = U[2::3]

            s   = np.array(stresses) if stresses else np.zeros((n, 6))
            sx  = s[:, 0]; sy = s[:, 1]; sz = s[:, 2]
            txy = s[:, 3]; tyz = s[:, 4]; tzx = s[:, 5]

            # Еквівалентне напруження (Von Mises)
            vm  = np.sqrt(0.5 * ((sx-sy)**2 + (sy-sz)**2 + (sz-sx)**2
                                 + 6*(txy**2 + tyz**2 + tzx**2)))

            xd = x0 + ux * scale_factor
            yd = y0 + uy * scale_factor
            zd = z0 + uz * scale_factor

            # --- 1. Формування Каркаса (Wireframe) ---
            lx0, ly0, lz0 = self._wireframe(x0.tolist(), y0.tolist(), z0.tolist(), nt_list)
            lxd, lyd, lzd = self._wireframe(xd.tolist(), yd.tolist(), zd.tolist(), nt_list)

            # --- 2. Формування Граней для Ізополів (Mesh3d) ---
            # Розбиваємо кожен гексаедр на трикутники (по 2 на кожну з 6 граней)
            I, J, K = [], [], []
            for el in nt_list:
                # Нижня грань
                I.extend([el[0], el[0]]); J.extend([el[1], el[2]]); K.extend([el[2], el[3]])
                # Верхня грань
                I.extend([el[4], el[4]]); J.extend([el[5], el[6]]); K.extend([el[6], el[7]])
                # Передня грань
                I.extend([el[0], el[0]]); J.extend([el[1], el[5]]); K.extend([el[5], el[4]])
                # Права грань
                I.extend([el[1], el[1]]); J.extend([el[2], el[6]]); K.extend([el[6], el[5]])
                # Задня грань
                I.extend([el[2], el[2]]); J.extend([el[3], el[7]]); K.extend([el[7], el[6]])
                # Ліва грань
                I.extend([el[3], el[3]]); J.extend([el[0], el[4]]); K.extend([el[4], el[7]])

            # Hover тексти
            hover = []
            for i in range(n):
                hover.append(
                    f'<b>Вузол {i}</b><br>'
                    f'────────────────<br>'
                    f'<b>Напруження:</b><br>'
                    f'Von Mises = <b>{vm[i]:.2e}</b><br>'
                    f'σX = {sx[i]:.2e} | τXY = {txy[i]:.2e}<br>'
                    f'σY = {sy[i]:.2e} | τYZ = {tyz[i]:.2e}<br>'
                    f'σZ = {sz[i]:.2e} | τZX = {tzx[i]:.2e}<br>'
                    f'────────────────<br>'
                    f'U={ux[i]:.2e}, V={uy[i]:.2e}, W={uz[i]:.2e}'
                )

            fig = go.Figure()

            # Trace 0: Початковий каркас
            fig.add_trace(go.Scatter3d(
                x=lx0, y=ly0, z=lz0, mode='lines', name='До деформації',
                line=dict(color='#FF0000', width=2), opacity=0.35, hoverinfo='skip',
            ))

            # Trace 1: Деформований каркас
            fig.add_trace(go.Scatter3d(
                x=lxd, y=lyd, z=lzd, mode='lines', name='Після деформації',
                line=dict(color='#2ecc71', width=2), hoverinfo='skip', visible=False
            ))

            # Trace 2: Початкові вузли (приховані)
            fig.add_trace(go.Scatter3d(
                x=x0, y=y0, z=z0, mode='markers', name='Початкові вузли',
                marker=dict(size=3, color='#7f8c8d', opacity=0.5), hoverinfo='skip', visible=False
            ))

            # Trace 3: Номери вузлів (приховані)
            fig.add_trace(go.Scatter3d(
                x=x0, y=y0, z=z0, mode='markers+text', name='Номери вузлів',
                text=[str(i) for i in range(n)], textposition='top center',
                textfont=dict(size=8, color='#2c3e50'), hoverinfo='skip', visible=False
            ))

            # Trace 4: Деформовані вузли (точки з інформацією)
            fig.add_trace(go.Scatter3d(
                x=xd, y=yd, z=zd, mode='markers', name='Деформовані вузли',
                marker=dict(size=3, color='#154a23', opacity=0.7),
                text=hover, hovertemplate='%{text}<extra></extra>', visible=False
            ))

            # Trace 5: 3D-Ізополя напружень (Von Mises)
            fig.add_trace(go.Mesh3d(
                x=xd, y=yd, z=zd,
                i=I, j=J, k=K,
                intensity=vm,              # Інтенсивність кольору базується на Von Mises
                colorscale='Jet',          # Класична FEA палітра (від синього до червоного)
                showscale=True,
                colorbar=dict(title='Von Mises<br>[Па]', x=0.85),
                name='Напруження Von Mises',
                hoverinfo='skip',
                flatshading=False,         # Згладжування кольорів
                visible=True
            ))

            # Інтерактивні кнопки перемикання режимів
            fig.update_layout(
                updatemenus=[dict(
                    type='buttons', direction='down',
                    x=0.0, xanchor='left', y=1.08, yanchor='top',
                    showactive=True,
                    buttons=[
                        dict(
                            label='🔴 Ізополя напружень',
                            method='update',
                            args=[{'visible': [True, False, False, False, False, True]}]
                        ),
                        dict(
                            label='🟩 Каркас деформації',
                            method='update',
                            args=[{'visible': [True, True, False, False, True, False]}]
                        ),
                        dict(
                            label='🔢 Показати номери вузлів',
                            method='update',
                            args=[{'visible': [True, True, False, True, True, False]}]
                        ),
                    ],
                    bgcolor='#ecf0f1', bordercolor='#bdc3c7', font=dict(size=11),
                )]
            )

            title = (f'Деформація та напруження  |  E = {E}  |  P = {P}  |  '
                     f'масштаб ×{scale_factor}  |  {len(nt_list)} ел., {n} вузлів')

            layout = self._base_layout(title)
            layout['margin'] = dict(l=0, r=90, b=40, t=100)
            fig.update_layout(**layout)

            return fig

    def _wireframe(self, nodes_x, nodes_y, nodes_z, nt_list):
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
                    i1, i2 = e
                    xl += [nodes_x[i1], nodes_x[i2], None]
                    yl += [nodes_y[i1], nodes_y[i2], None]
                    zl += [nodes_z[i1], nodes_z[i2], None]
        return xl, yl, zl

    def _base_layout(self, title):
        ax = dict(showbackground=False, showgrid=True,
                  gridcolor='rgba(180,180,180,0.3)', zeroline=True)
        return dict(
            title=dict(text=title, x=0.5, font=dict(size=12)),
            scene=dict(
                xaxis=dict(title='X', **ax),
                yaxis=dict(title='Y', **ax),
                zaxis=dict(title='Z', **ax),
                aspectmode='data',
                camera=dict(eye=dict(x=1.8, y=-1.8, z=1.4)),
            ),
            legend=dict(
                x=0.01, y=0.99,
                bgcolor='rgba(255,255,255,0.85)',
                bordercolor='rgba(0,0,0,0.15)',
                borderwidth=1, font=dict(size=11),
                itemsizing='constant',
            ),
            margin=dict(l=0, r=90, b=20, t=60),
        )