from task import constants

class MeshGenerator:
    """
    Клас відповідає виключно за генерацію сітки скінченних елементів, 
    створення глобальних вузлів (AKT) та матриці зв'язності (NT).
    """
    def __init__(self):
        pass

    def create_points(self, a, b, c, na, nb, nc):
        """
        Розбиває область на масив елементів ("кубиків").
        """
        result = []
        step_a = a / na
        step_b = b / nb
        step_c = c / nc
        
        for k in range(nc):
            for j in range(nb):
                for i in range(na):
                    cube = self.create_cube(i * step_a, (i + 1) * step_a,
                                            j * step_b, (j + 1) * step_b,
                                            k * step_c, (k + 1) * step_c)
                    result.append(cube)
        return result

    def create_cube(self, a_start, a_end, b_start, b_end, c_start, c_end):
        """
        Генерує 20 локальних точок для одного скінченного елемента,
        СТРОГО відповідно до нової матриці LOCAL_NODE_COORDS_3D.
        """
        # Знаходимо координати середин (mid)
        a_mid = a_start + (a_end - a_start) / 2
        b_mid = b_start + (b_end - b_start) / 2
        c_mid = c_start + (c_end - c_start) / 2

        # 1-4: кутові низ
        # 5-8: кутові верх
        # 9-12: серединні низ
        # 13-16: серединні верх
        # 17-20: вертикальні
        
        x = [
            a_start, a_end, a_end, a_start,  # 1-4
            a_start, a_end, a_end, a_start,  # 5-8
            a_mid, a_end, a_mid, a_start,    # 9-12
            a_mid, a_end, a_mid, a_start,    # 13-16
            a_start, a_end, a_end, a_start   # 17-20
        ]
        
        y = [
            b_start, b_start, b_end, b_end,  # 1-4
            b_start, b_start, b_end, b_end,  # 5-8
            b_start, b_mid, b_end, b_mid,    # 9-12
            b_start, b_mid, b_end, b_mid,    # 13-16
            b_start, b_start, b_end, b_end   # 17-20
        ]
        
        z = [
            c_start, c_start, c_start, c_start,  # 1-4
            c_end, c_end, c_end, c_end,          # 5-8
            c_start, c_start, c_start, c_start,  # 9-12
            c_end, c_end, c_end, c_end,          # 13-16
            c_mid, c_mid, c_mid, c_mid           # 17-20
        ]
        
        result = []
        for i in range(constants.NODES_PER_ELEMENT):
            result.append([x[i], y[i], z[i]])
        return result

    def create_cube_1(self, a_start, a_end, b_start, b_end, c_start, c_end):
        """
        Генерує 20 локальних точок для одного скінченного елемента.
        """
        a_size = a_end - a_start
        b_size = b_end - b_start
        c_size = c_end - c_start

        x = [a_start,  a_end,  a_end,  a_start,  a_start,  a_end,  a_end,  a_start,
             a_start + a_size / 2,  a_end,  a_start + a_size / 2,  a_start,
             a_start,  a_end,  a_end,  a_start,
             a_start + a_size / 2,  a_end,  a_start + a_size / 2,  a_start]

        y = [b_end,    b_end,    b_start,  b_start,  b_end,    b_end,    b_start,  b_start,
             b_end,    b_start + b_size / 2,  b_start,  b_start + b_size / 2,
             b_end,    b_end,    b_start,  b_start,
             b_end,    b_start + b_size / 2,  b_start,  b_start + b_size / 2]
        
        z = [c_start,  c_start,  c_start,  c_start,  c_end,  c_end,  c_end,  c_end,
             c_start,  c_start,  c_start,  c_start,
             c_start + c_size / 2,  c_start + c_size / 2,  c_start + c_size / 2,  c_start + c_size / 2,
             c_end,  c_end,  c_end,  c_end]
        
        result = []
        for i in range(constants.NODES_PER_ELEMENT):
            result.append([x[i], y[i], z[i]])
        return result
    
    # def create_cube(self, a_start, a_end, b_start, b_end, c_start, c_end):
    #     """
    #     Генерує 20 локальних точок для одного скінченного елемента.
    #     """
    #     a_size = a_end - a_start
    #     b_size = b_end - b_start
    #     c_size = c_end - c_start

    #     x = [a_start,  a_end,  a_end,  a_start,  a_start,  a_end,  a_end,  a_start,
    #          a_start + a_size / 2,  a_end,  a_start + a_size / 2,  a_start,
    #          a_start,  a_end,  a_end,  a_start,
    #          a_start + a_size / 2,  a_end,  a_start + a_size / 2,  a_start]
        
    #     y = [b_start,  b_start,  b_end,  b_end,  b_start,  b_start,  b_end,  b_end,
    #          b_start,  b_start + b_size / 2,  b_end,  b_start + b_size / 2,
    #          b_start,  b_start,  b_end,  b_end,
    #          b_start,  b_start + b_size / 2,  b_end,  b_start + b_size / 2]
        
    #     z = [c_start,  c_start,  c_start,  c_start,  c_end,  c_end,  c_end,  c_end,
    #          c_start,  c_start,  c_start,  c_start,
    #          c_start + c_size / 2,  c_start + c_size / 2,  c_start + c_size / 2,  c_start + c_size / 2,
    #          c_end,  c_end,  c_end,  c_end]
        
    #     result = []
    #     for i in range(constants.NODES_PER_ELEMENT):
    #         result.append([x[i], y[i], z[i]])
    #     return result

    def separate_point(self, a, b, c, na, nb, nc):
        """
        Створює глобальний масив унікальних вузлів (масив AKT).
        """
        result = []
        step_a = a / na
        step_b = b / nb
        step_c = c / nc

        for k in range(2 * nc + 1):
            if k % 2 == 0:
                for j in range(2 * nb + 1):
                    if j % 2 == 0:
                        for i in range(2 * na + 1):
                            result.append([i * step_a / 2, j * step_b / 2, k * step_c / 2])
                    else:
                        for i in range(na + 1):
                            result.append([i * step_a, j * step_b / 2, k * step_c / 2])
            else:
                for j in range(nb + 1):
                    for i in range(na + 1):
                        result.append([i * step_a, j * step_b, k * step_c / 2])
        return result

    def NT_transform(self, akt, elements):
        """
        Формує матрицю зв'язності (інцидентності) NT.
        """
        NT = []
        node_map = self.create_node_map(akt)
        
        for el in elements:
            el_indices = []
            for node in el:
                idx = self.find_node_index(node, node_map)
                
                if idx is not None:
                    el_indices.append(idx)
                else:
                    raise ValueError(f"Node {node} not found in AKT!")
            NT.append(el_indices)
            
        return NT
    
    def create_node_map(self, AKT):
        """Створює карту пошуку індексів вузлів."""
        return {
            (round(node[0], 7), round(node[1], 7), round(node[2], 7)): i 
            for i, node in enumerate(AKT)
        }

    def find_node_index(self, node, node_map):
        """Пошук індексу конкретного вузла через карту."""
        key = (round(node[0], 7), round(node[1], 7), round(node[2], 7))
        return node_map.get(key)