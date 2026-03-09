import numpy as np

from task import constants

class ShapeFunctionsMath:
    """
    Клас відповідає за математичний апарат МСЕ.
    Обчислює похідні функцій форми для 20-вузлового елемента.
    """
    
    def __init__(self):
        """
        Ініціалізує клас для роботи з математичним апаратом МСЕ.
        """
        pass

    def DFIABG_Create(self):
        """
        Генерує масив похідних функцій форми у всіх 27 точках інтегрування Гауса.
        Повертає тривимірний масив (27 точок Гауса х 20 вузлів х 3 похідні).
        """
        result = []
        for gamma in constants.GAUSS_POINTS:
            for beta in constants.GAUSS_POINTS:
                for alpha in constants.GAUSS_POINTS:
                    a = []
                    for i, point in enumerate(constants.LOCAL_NODE_COORDS_3D):
                        # Індекси 0-7 - це кутові вузли, 8-19 - серединні вузли
                        if i > 7:
                            a.append(self.DFIABD_center_side(alpha, beta, gamma, point[0], point[1], point[2]))
                        else:
                            a.append(self.DFIABD_angle(alpha, beta, gamma, point[0], point[1], point[2]))
                    result.append(a)
        return result

    def DFIABD_angle(self, alpha, beta, gamma, alpha_i, beta_i, gamma_i):
        """
        Обчислює похідні для КУТОВИХ вузлів (1-8).
        """
        result = [
            (1 / 8) * (1 + beta * beta_i) * (1 + gamma * gamma_i) *
            (alpha_i * (-2 + alpha * alpha_i + gamma * gamma_i + beta * beta_i) + alpha_i * (1 + alpha * alpha_i)),

            (1 / 8) * (1 + alpha * alpha_i) * (1 + gamma * gamma_i) *
            (beta_i * (-2 + alpha * alpha_i + gamma * gamma_i + beta * beta_i) + beta_i * (1 + beta * beta_i)),

            (1 / 8) * (1 + beta * beta_i) * (1 + alpha * alpha_i) *
            (gamma_i * (-2 + alpha * alpha_i + gamma * gamma_i + beta * beta_i) + gamma_i * (1 + gamma * gamma_i))
        ]
        return result

    def DFIABD_center_side(self, alpha, beta, gamma, alpha_i, beta_i, gamma_i):
        """
        Обчислює похідні для СЕРЕДИННИХ вузлів (9-20).
        """
        result = [
            (1 / 4) * (1 + beta * beta_i) * (1 + gamma * gamma_i) *
            (alpha_i * (
                    -beta_i * beta_i * gamma_i * gamma_i * alpha * alpha
                    - beta * beta * gamma_i * gamma_i * alpha_i * alpha_i
                    - beta_i * beta_i * gamma * gamma * alpha_i * alpha_i + 1) -
             (2 * beta_i * beta_i * gamma_i * gamma_i * alpha) * (alpha * alpha_i + 1)),

            (1 / 4) * (1 + alpha * alpha_i) * (1 + gamma * gamma_i) *
            (beta_i * (
                    -beta_i * beta_i * gamma_i * gamma_i * alpha * alpha
                    - beta * beta * gamma_i * gamma_i * alpha_i * alpha_i
                    - beta_i * beta_i * gamma * gamma * alpha_i * alpha_i + 1) -
             (2 * beta * gamma_i * gamma_i * alpha_i * alpha_i) * (beta_i * beta + 1)),

            (1 / 4) * (1 + beta * beta_i) * (1 + alpha * alpha_i) *
            (gamma_i * (
                    -beta_i * beta_i * gamma_i * gamma_i * alpha * alpha
                    - beta * beta * gamma_i * gamma_i * alpha_i * alpha_i
                    - beta_i * beta_i * gamma * gamma * alpha_i * alpha_i + 1) -
             (2 * beta_i * beta_i * gamma * alpha_i * alpha_i) * (gamma * gamma_i + 1))
        ]
        return result
    
    import numpy as np

    def create_jacobian_for_element(self, element_coords, dfiabg_matrix):
        """
        Створює 27 матриць Якобі (3x3) для ОДНОГО скінченного елемента.
        
        :param element_coords: Координати 20 вузлів елемента [[x1, y1, z1], ..., [x20, y20, z20]]
        :param dfiabg_matrix: Ідеальні похідні (27 точок Гауса x 20 вузлів x 3 напрямки)
        :return: Список із 27 матриць Якобі.
        """
        jacobians = []
        
        for gauss_idx in range(constants.GAUSS_POINTS_COUNT):
            J = np.zeros((3, 3))
            
            for node_idx in range(constants.NODES_PER_ELEMENT):
                x, y, z = element_coords[node_idx]
                dphi_da, dphi_db, dphi_dg = dfiabg_matrix[gauss_idx][node_idx]
                
                J[0, 0] += x * dphi_da;  J[0, 1] += y * dphi_da;  J[0, 2] += z * dphi_da
                J[1, 0] += x * dphi_db;  J[1, 1] += y * dphi_db;  J[1, 2] += z * dphi_db
                J[2, 0] += x * dphi_dg;  J[2, 1] += y * dphi_dg;  J[2, 2] += z * dphi_dg
                
            jacobians.append(J.tolist())
            
        return jacobians

    def calculate_dfixyz_for_element(self, jacobians, dfiabg_matrix):
        """
        Розв'язує СЛАР для знаходження реальних похідних DFIXYZ для ОДНОГО елемента.
        
        :param jacobians: Список із 27 матриць Якобі для цього елемента.
        :param dfiabg_matrix: Ідеальні похідні.
        :return: Реальні похідні DFIXYZ (27 точок x 20 вузлів x 3 напрямки)
        """
        dfixyz_element = []
        
        for gauss_idx in range(constants.GAUSS_POINTS_COUNT):
            J_matrix = np.array(jacobians[gauss_idx])
            dfixyz_gauss_point = []
            
            for node_idx in range(constants.NODES_PER_ELEMENT):
                dphi_local = np.array(dfiabg_matrix[gauss_idx][node_idx])
                
                # Розв'язуємо систему J * DFIXYZ = DFIABG за допомогою numpy
                dphi_global = np.linalg.solve(J_matrix, dphi_local)
                
                dfixyz_gauss_point.append(dphi_global.tolist())
                
            dfixyz_element.append(dfixyz_gauss_point)
            
        return dfixyz_element

    def calculate_determinant(self, a):
        """
        Обчислює визначник матриці 3x3 (Масштабний коефіцієнт |J|).
        """
        return np.linalg.det(a)

    def calc_MGE(self, DFIXYZ_cast, determinant_list, c_list, lambda_val, nu_val, mu_val):
        matrix_a11 = []
        matrix_a22 = []
        matrix_a33 = []
        matrix_a12 = []
        matrix_a13 = []
        matrix_a23 = []
        for i in range(constants.NODES_PER_ELEMENT):
            line_of_matrix_a11 = []
            line_of_matrix_a22 = []
            line_of_matrix_a33 = []
            line_of_matrix_a12 = []
            line_of_matrix_a13 = []
            line_of_matrix_a23 = []
            for j in range(constants.NODES_PER_ELEMENT):
                a11 = []
                a22 = []
                a33 = []
                a12 = []
                a13 = []
                a23 = []
                general_index = 0
                for m in c_list:
                    for n in c_list:
                        for k in c_list:
                            dfi = DFIXYZ_cast[general_index]
                            a11.append(m * n * k *
                                       (lambda_val * (1 - nu_val) * (dfi[i][0] * dfi[j][0]) +
                                        mu_val * ((dfi[i][1] * dfi[j][1]) + (dfi[i][2] * dfi[j][2]))) *
                                       determinant_list[general_index])

                            a22.append(m * n * k *
                                       (lambda_val * (1 - nu_val) * (dfi[i][1] * dfi[j][1]) +
                                        mu_val * ((dfi[i][0] * dfi[j][0]) + (dfi[i][2] * dfi[j][2]))) *
                                       determinant_list[general_index])

                            a33.append(m * n * k *
                                       (lambda_val * (1 - nu_val) * (dfi[i][2] * dfi[j][2]) +
                                        mu_val * ((dfi[i][0] * dfi[j][0]) + (dfi[i][1] * dfi[j][1]))) *
                                       determinant_list[general_index])

                            a12.append(m * n * k * (lambda_val * nu_val * (dfi[i][0] * dfi[j][1]) +
                                                    mu_val * (dfi[i][1] * dfi[j][0])) * determinant_list[general_index])

                            a13.append(m * n * k * (lambda_val * nu_val * (dfi[i][0] * dfi[j][2]) +
                                                    mu_val * (dfi[i][2] * dfi[j][0])) * determinant_list[general_index])

                            a23.append(m * n * k * (lambda_val * nu_val * (dfi[i][1] * dfi[j][2]) +
                                                    mu_val * (dfi[i][2] * dfi[j][1])) * determinant_list[general_index])
                            general_index += 1
                line_of_matrix_a11.append(sum(a11))
                line_of_matrix_a22.append(sum(a22))
                line_of_matrix_a33.append(sum(a33))
                line_of_matrix_a12.append(sum(a12))
                line_of_matrix_a13.append(sum(a13))
                line_of_matrix_a23.append(sum(a23))
            matrix_a22.append(line_of_matrix_a22)
            matrix_a33.append(line_of_matrix_a33)
            matrix_a11.append(line_of_matrix_a11)
            matrix_a12.append(line_of_matrix_a12)
            matrix_a13.append(line_of_matrix_a13)
            matrix_a23.append(line_of_matrix_a23)

        matrix1 = np.array(matrix_a11)
        matrix2 = np.array(matrix_a12)
        matrix3 = np.array(matrix_a13)
        matrix4 = np.array(matrix_a22)
        matrix5 = np.array(matrix_a23)
        matrix6 = np.array(matrix_a33)

        big_matrix = np.zeros((60, 60))

        big_matrix[:20, :20] = matrix1
        big_matrix[:20, 20:40] = matrix2
        big_matrix[:20, 40:] = matrix3
        big_matrix[20:40, :20] = matrix2.T
        big_matrix[20:40, 20:40] = matrix4
        big_matrix[20:40, 40:] = matrix5
        big_matrix[40:, :20] = matrix3.T
        big_matrix[40:, 20:40] = matrix5.T
        big_matrix[40:, 40:] = matrix6

        big_matrix = big_matrix.tolist()
        return big_matrix
    
    def save_dfiabg_to_txt(self, dfiabg_matrix, filename="statics/DFIABG.txt"):
        """
        Зберігає матрицю похідних DFIABG у зручному текстовому форматі.
        
        :param dfiabg_matrix: Тривимірний масив похідних.
        :param filename: Назва файлу для збереження.
        """
        import os
        filepath = os.path.abspath(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Матриця похідних функцій форми (DFIABG)\n")
            f.write("="*50 + "\n\n")
            
            for gauss_idx, gauss_point in enumerate(dfiabg_matrix):
                f.write(f"--- Точка Гауса {gauss_idx + 1} ---\n")
                for node_idx, node_derivs in enumerate(gauss_point):
                    d_alpha = node_derivs[0]
                    d_beta = node_derivs[1]
                    d_gamma = node_derivs[2]
                    
                    f.write(f"  Вузол {node_idx + 1:2d}: "
                            f"dPhi/da = {d_alpha:10.6f} | "
                            f"dPhi/db = {d_beta:10.6f} | "
                            f"dPhi/dg = {d_gamma:10.6f}\n")
                f.write("\n")
                
        print(f"Матриця DFIABG успішно збережена у файл: {filepath}")

    def save_dfixyz_to_txt(self, dfixyz_element, filename="statics/DFIXYZ_element_0.txt", element_id=0):
        """
        Зберігає матрицю реальних похідних DFIXYZ для ОДНОГО елемента у текстовий файл.
        
        :param dfixyz_element: Матриця DFIXYZ (27 точок Гауса x 20 вузлів x 3 осі).
        :param filename: Назва файлу для збереження.
        :param element_id: Номер елемента (для підпису всередині файлу).
        """
        import os
        filepath = os.path.abspath(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Матриця РЕАЛЬНИХ похідних (DFIXYZ) для Елемента №{element_id}\n")
            f.write("="*60 + "\n\n")
            
            for gauss_idx, gauss_point in enumerate(dfixyz_element):
                f.write(f"--- Точка Гауса {gauss_idx + 1} ---\n")
                for node_idx, node_derivs in enumerate(gauss_point):
                    d_x = node_derivs[0]
                    d_y = node_derivs[1]
                    d_z = node_derivs[2]
                    
                    f.write(f"  Вузол {node_idx + 1:2d}: "
                            f"dPhi/dx = {d_x:12.6f} | "
                            f"dPhi/dy = {d_y:12.6f} | "
                            f"dPhi/dz = {d_z:12.6f}\n")
                f.write("\n")
                
        print(f"Матриця DFIXYZ для елемента {element_id} успішно збережена у файл: {filepath}")