from task import constants


class MeshGenerator:
    """
    Клас відповідає за генерацію сітки скінченних елементів (тріангуляцію).
    """

    def __init__(self):
        pass

    def create_points(self, a, b, c, na, nb, nc):
        """
        Генерує список усіх скінченних елементів у вигляді груп по 20 точок.

        Область a×b×c ділиться на na×nb×nc елементів-паралелепіпедів
        (рис. 1а практикуму). Для кожного «кубика» викликається create_cube,
        яка розставляє 20 вузлів (8 кутових + 12 серединних) згідно рис. 2.

        Порядок обходу: спочатку по x (i), потім по y (j), потім по z (k) —
        тобто «шарами» знизу вгору.

        Повертає: список з na*nb*nc елементів, кожен — список із 20 точок [x,y,z].
        """
        result = []
        step_a = a / na
        step_b = b / nb
        step_c = c / nc

        for k in range(nc):
            for j in range(nb):
                for i in range(na):
                    cube = self.create_cube(
                        i * step_a, (i + 1) * step_a,
                        j * step_b, (j + 1) * step_b,
                        k * step_c, (k + 1) * step_c
                    )
                    result.append(cube)
        return result

    def create_cube(self, a_start, a_end, b_start, b_end, c_start, c_end):
        """
        Генерує 20 локальних вузлів одного скінченного елемента.

        Розташування вузлів відповідає рис. 2 практикуму та масиву
        LOCAL_NODE_COORDS_3D з constants.py (формула 24):
          вузли  1- 4: кутові нижньої грані (z = c_start)
          вузли  5- 8: кутові верхньої грані (z = c_end)
          вузли  9-12: серединні нижньої грані (середина ребра, z = c_start)
          вузли 13-16: серединні верхньої грані (середина ребра, z = c_end)
          вузли 17-20: вертикальні серединні (середина бічного ребра, z = c_mid)

        Серединні вузли необхідні для апроксимації другого порядку — функції
        форми (формула 24) є квадратичними поліномами, що забезпечує вищу
        точність порівняно з лінійними елементами.
        """
        a_mid = a_start + (a_end - a_start) / 2
        b_mid = b_start + (b_end - b_start) / 2
        c_mid = c_start + (c_end - c_start) / 2

        x = [
            a_start, a_end, a_end, a_start,    # вузли 1-4:  кутові нижня грань
            a_start, a_end, a_end, a_start,    # вузли 5-8:  кутові верхня грань
            a_mid,   a_end, a_mid, a_start,    # вузли 9-12: серединні нижньої грані
            a_mid,   a_end, a_mid, a_start,    # вузли 13-16: серединні верхньої грані
            a_start, a_end, a_end, a_start     # вузли 17-20: вертикальні серединні
        ]

        y = [
            b_start, b_start, b_end, b_end,    # вузли 1-4
            b_start, b_start, b_end, b_end,    # вузли 5-8
            b_start, b_mid,   b_end, b_mid,    # вузли 9-12
            b_start, b_mid,   b_end, b_mid,    # вузли 13-16
            b_start, b_start, b_end, b_end     # вузли 17-20
        ]

        z = [
            c_start, c_start, c_start, c_start,  # вузли 1-4
            c_end,   c_end,   c_end,   c_end,    # вузли 5-8
            c_start, c_start, c_start, c_start,  # вузли 9-12
            c_end,   c_end,   c_end,   c_end,    # вузли 13-16
            c_mid,   c_mid,   c_mid,   c_mid     # вузли 17-20
        ]

        return [[x[i], y[i], z[i]] for i in range(constants.NODES_PER_ELEMENT)]

    def separate_point(self, a, b, c, na, nb, nc):
        """
        Формує масив AKT — глобальний масив координат усіх унікальних вузлів.

        Формула (7) практикуму: AKT [N × 3], де N — загальна кількість вузлів.

        Для сітки na×nb×nc елементів кількість вузлів (N) дорівнює:
          N = (2*na+1)*(2*nb+1)*(nc+1) + (na+1)*(nb+1)*nc

        Алгоритм: обхід «шарами» по z (k). Парний шар (k%2==0, z = k*step/2) має
        повні ряди і ряди тільки по вузлах елемента. Непарний шар (k%2==1,
        між гранями) — лише кутові/серединні вузли ребер.

        Вузли додаються по порядку — їх індекс у цьому масиві і є «глобальним
        номером» вузла. NT потім відображає локальні номери (1-20) у ці
        глобальні індекси.
        """
        result = []
        step_a = a / na
        step_b = b / nb
        step_c = c / nc

        for k in range(2 * nc + 1):
            if k % 2 == 0:
                # ── ПАРНИЙ ШАР k: горизонтальна грань (z = k*step_c/2) ──────────
                # Містить 8 вузлів: 4 кутових + 4 серединних ребер.
                # Внутрішній цикл по j будує один горизонтальний шар "зиґзаґом":
                #   j парний  → 2*na+1 точок (кутові + серединні по x)
                #   j непарний → na+1 точок  (серединні по y)
                # Разом: (nb+1)*(2*na+1) + nb*(na+1) точок на парний шар.
                # Для na=nb=1: 2*3 + 1*2 = 8 точок (нижня або верхня грань елемента).
                for j in range(2 * nb + 1):
                    if j % 2 == 0:
                        for i in range(2 * na + 1):
                            result.append([i * step_a / 2, j * step_b / 2, k * step_c / 2])
                    else:
                        for i in range(na + 1):
                            result.append([i * step_a, j * step_b / 2, k * step_c / 2])
            else:
                # ── НЕПАРНИЙ ШАР k: проміжна висота z = k*step_c/2 ──────────────
                # Це вузли на серединах ВЕРТИКАЛЬНИХ ребер — вузли 13-16 на Рис. 2
                # Для na=nb=1: 2*2 = 4 точки → рівно 4 вертикальні серединні вузли.
                for j in range(nb + 1):
                    for i in range(na + 1):
                        result.append([i * step_a, j * step_b, k * step_c / 2])
        return result  # AKT: N × 3  — координати [x, y, z] кожного вузла

    def NT_transform(self, akt, elements):
        """
        Формує матрицю зв'язності NT (M × 20) (формула 21 практикуму).

        NT[j] — список із 20 глобальних індексів вузлів j-го елемента.
        NT[i,j] = глобальний номер i-го локального вузла j-го елемента.

        Принцип: для кожного з 20 вузлів елемента шукаємо його координати
        в масиві AKT і записуємо знайдений глобальний індекс.

        Це «клей» між локальними обчисленнями на елементі (MGE, FE) та
        глобальними матрицями (MG, F) — заняття 8 практикуму.
        Спільні вузли сусідніх елементів мають один і той самий глобальний
        номер → їхні внески в MGE підсумовуються в одному місці MG.
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
        """
        Будує словник {координати → глобальний індекс} для швидкого пошуку.

        Координати округлюються до 7 знаків для уникнення помилок з float.
        """
        return {
            (round(node[0], 7), round(node[1], 7), round(node[2], 7)): i
            for i, node in enumerate(AKT)
        }

    def find_node_index(self, node, node_map):
        """Повертає глобальний індекс вузла за його координатами."""
        key = (round(node[0], 7), round(node[1], 7), round(node[2], 7))
        return node_map.get(key)
