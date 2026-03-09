import plotly.graph_objects as go

class MeshVisualizer:
    def __init__(self):
        self.node_color = 'red'
        self.node_size = 3
        self.text_color = 'darkred'

    def plot_initial_mesh(self, global_nodes, nt_list):
        x_points = [node[0] for node in global_nodes]
        y_points = [node[1] for node in global_nodes]
        z_points = [node[2] for node in global_nodes]

        num_nodes = len(x_points)
        is_large_mesh = num_nodes > 800
        
        node_mode = 'markers' if is_large_mesh else 'markers+text'
        node_numbers = [str(i) for i in range(num_nodes)] if not is_large_mesh else None

        fig = go.Figure()

        # 1. ВУЗЛИ
        fig.add_trace(go.Scatter3d(
            x=x_points, y=y_points, z=z_points,
            mode=node_mode,
            name='Вузли',
            marker=dict(size=self.node_size if not is_large_mesh else 1, color=self.node_color),
            text=node_numbers,
            textposition="top center",
            hoverinfo='x+y+z'
        ))

        # 2. КАРКАС
        lx, ly, lz = self.build_wireframe_coords_optimized(x_points, y_points, z_points, nt_list)
        fig.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz,
            mode='lines',
            name='Сітка',
            line=dict(color='blue', width=1),
            opacity=0.4
        ))

        axis_template = dict(
            showbackground=False,
            showgrid=True,   
            gridcolor='rgba(200, 200, 200, 0.8)',
            showline=True,  
            zeroline=True,  
        )

        updatemenus = [
            dict(
                type="buttons",
                direction="left",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=0.9,
                yanchor="top",
                buttons=list([
                    dict(
                        label="Номери вкл",
                        method="restyle",
                        args=[{"mode": "markers+text"}, [0]]
                    ),
                    dict(
                        label="Номери викл",
                        method="restyle",
                        args=[{"mode": "markers"}, [0]]
                    ),
                ]),
            ),
        ]

        fig.update_layout(
            title=f"МСЕ Сітка: {len(nt_list)} елементів, {num_nodes} вузлів",
            updatemenus=updatemenus,
            scene=dict(
                xaxis=dict(title='X', **axis_template),
                yaxis=dict(title='Y', **axis_template),
                zaxis=dict(title='Z', **axis_template),
                aspectmode='data', 
                camera=dict(       # Початковий кут огляду
                    eye=dict(x=2, y=-2, z=1.7)
                )
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        return fig

    def build_wireframe_coords_optimized(self, nodes_x, nodes_y, nodes_z, nt_list):
        """Збирає унікальні ребра, щоб не малювати одну лінію двічі"""
        x_lines, y_lines, z_lines = [], [], []
        unique_edges = set()

        # Ребра для 20-вузлового елемента (тільки основні контури для швидкості)
        # З'єднуємо кути: 0-1-2-3-0 (низ), 4-5-6-7-4 (верх) та стійки 0-4, 1-5, 2-6, 3-7
        edge_map = [
            (0,1), (1,2), (2,3), (3,0), # низ
            (4,5), (5,6), (6,7), (7,4), # верх
            (0,4), (1,5), (2,6), (3,7)  # вертикалі
        ]

        for el in nt_list:
            for start, end in edge_map:
                edge = tuple(sorted((el[start], el[end])))
                if edge not in unique_edges:
                    unique_edges.add(edge)
                    
                    idx1, idx2 = edge
                    x_lines.extend([nodes_x[idx1], nodes_x[idx2], None])
                    y_lines.extend([nodes_y[idx1], nodes_y[idx2], None])
                    z_lines.extend([nodes_z[idx1], nodes_z[idx2], None])

        return x_lines, y_lines, z_lines