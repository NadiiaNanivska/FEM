class BoundaryConditionManager:
    """
    Клас відповідає за проекцію крайових умов задачі теорії пружності
    на скінченно-елементну модель (заняття 4, практикум).
    """

    def __init__(self):
        pass

    def ZU_Chose(self, eleme, axis=2, side='min'):
        """
        Формує масив ZU — список координат вузлів на закріпленій грані (формула 30).

        Фізична задача (практикум, п.2): нижня грань паралелепіпеда жорстко
        закріплена → переміщення всіх трьох компонент (uₓ, uᵧ, u_z) у цих
        вузлах дорівнюють нулю (умова 4).

        За замовчуванням: axis=2 (вісь Z), side='min' (нижня грань, z=0).
        Можна задати будь-яку грань паралелепіпеда.

        Параметри:
          eleme — список координат усіх вузлів [AKT]
          axis  — перпендикулярна вісь: 0=X, 1=Y, 2=Z
          side  — 'min' або 'max' — яка крайня грань

        Повертає: список координат [[x,y,z], ...] закріплених вузлів.
        Ці координати потім порівнюються з AKT у MG_Create для встановлення
        штрафних значень на діагоналі (заняття 10, спосіб 2).
        """
        if side == 'min':
            target_val = min([node[axis] for node in eleme])
        elif side == 'max':
            target_val = max([node[axis] for node in eleme])
        else:
            raise ValueError("Параметр side має бути 'min' або 'max'")

        return [node for node in eleme if node[axis] == target_val]

    def ZP_Chose(self, element_nodes, axis, side):
        """
        Знаходить 8 вузлів на навантаженій грані одного елемента (формула 31).

        Кожна грань 20-вузлового елемента містить 8 вузлів:
          4 кутових + 4 серединних на середині ребер (рис. 4 практикуму).

        Ці 8 точок передаються у FE_Calc() як ZP_cast для обчислення
        компонент нормалі і, відповідно, вектора навантаження FE (форм. 44).

        Параметри:
          element_nodes — координати 20 вузлів одного елемента
          axis  — нормаль до навантаженої грані: 0=X, 1=Y, 2=Z
          side  — 'max' (верхня грань) або 'min' (нижня)

        Повертає: список із 8 координат [[x,y,z], ...], або [] якщо грань
        не знайдена (не належить навантаженій стороні паралелепіпеда).
        """
        if side == 'min':
            target_val = min([node[axis] for node in element_nodes])
        elif side == 'max':
            target_val = max([node[axis] for node in element_nodes])
        else:
            raise ValueError("Параметр side має бути 'min' або 'max'")

        face_nodes = [node for node in element_nodes if round(node[axis], 6) == round(target_val, 6)]

        if len(face_nodes) != 8:
            return []

        return face_nodes
