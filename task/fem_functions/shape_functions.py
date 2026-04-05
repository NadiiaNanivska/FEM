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
    
    def PSINT_angel(self, eta, tau, eta_i, tau_i):
        result = [
            (1 / 4) * (tau * tau_i + 1) * (eta_i * (eta_i * eta + tau_i * tau - 1) + eta_i * (eta_i * eta + 1)),
            (1 / 4) * (eta_i * eta + 1) * (tau_i * (eta_i * eta + tau_i * tau - 1) + tau_i * (tau_i * tau + 1))
        ]
        return result

    def PSINT_57(self, eta, tau, eta_i, tau_i):
        result = [
            (-tau * tau_i - 1) * eta,
            (1 / 2) * (1 - eta * eta) * tau_i
        ]
        return result

    def PSINT_68(self, eta, tau, eta_i, tau_i):
        result = [
            (1 / 2) * (1 - tau * tau) * eta_i,
            (-eta * eta_i - 1) * tau
        ]
        return result

    def PSINT_angel_main(self, eta, tau, eta_i, tau_i):
        result = (1 / 4) * (tau * tau_i + 1) * (eta * eta_i + 1) * (eta * eta_i + tau_i * tau - 1)
        return result

    def PSINT_57_main(self, eta, tau, eta_i, tau_i):
        result = (1 / 2) * (-eta * eta + 1) * (tau_i * tau + 1)
        return result

    def PSINT_68_main(self, eta, tau, eta_i, tau_i):
        result = (1 / 2) * (-tau * tau + 1) * (eta_i * eta + 1)
        return result

    def DEPSITE(self):
        result = []
        for eta in constants.GAUSS_POINTS:
            for tau in constants.GAUSS_POINTS:
                a = []
                for point in constants.LOCAL_POINTS_2D:
                    if constants.LOCAL_POINTS_2D.index(point) < 4:
                        a.append(self.PSINT_angel(eta, tau, point[0], point[1]))
                    elif constants.LOCAL_POINTS_2D.index(point) == 4 or constants.LOCAL_POINTS_2D.index(point) == 6:
                        a.append(self.PSINT_57(eta, tau, point[0], point[1]))
                    elif constants.LOCAL_POINTS_2D.index(point) == 5 or constants.LOCAL_POINTS_2D.index(point) == 7:
                        a.append(self.PSINT_68(eta, tau, point[0], point[1]))
                result.append(a)
        return result

    def DxyzDnt(self, xyz):
        result = []
        depsite = self.DEPSITE()
        index_for_depsite = 0
        for eta in constants.GAUSS_POINTS:
            for tau in constants.GAUSS_POINTS:
                summ_x_eta = []
                summ_y_eta = []
                summ_z_eta = []
                summ_x_tau = []
                summ_y_tau = []
                summ_z_tau = []
                for index_of_nt, point in enumerate(xyz):
                    summ_x_eta.append(point[0] * depsite[index_for_depsite][index_of_nt][0])
                    summ_y_eta.append(point[1] * depsite[index_for_depsite][index_of_nt][0])
                    summ_z_eta.append(point[2] * depsite[index_for_depsite][index_of_nt][0])
                    summ_x_tau.append(point[0] * depsite[index_for_depsite][index_of_nt][1])
                    summ_y_tau.append(point[1] * depsite[index_for_depsite][index_of_nt][1])
                    summ_z_tau.append(point[2] * depsite[index_for_depsite][index_of_nt][1])
                result.append([
                    [sum(summ_x_eta), sum(summ_x_tau)],
                    [sum(summ_y_eta), sum(summ_y_tau)],
                    [sum(summ_z_eta), sum(summ_z_tau)]
                ])
                index_for_depsite += 1
        return result

    def DEPSIxyzDEnt(self):
        result = []
        for eta in constants.GAUSS_POINTS:
            for tau in constants.GAUSS_POINTS:
                a = []
                for point in constants.LOCAL_POINTS_2D:
                    if constants.LOCAL_POINTS_2D.index(point) < 4:
                        a.append(self.PSINT_angel_main(eta, tau, point[0], point[1]))
                    elif constants.LOCAL_POINTS_2D.index(point) == 4 or constants.LOCAL_POINTS_2D.index(point) == 6:
                        a.append(self.PSINT_57_main(eta, tau, point[0], point[1]))
                    elif constants.LOCAL_POINTS_2D.index(point) == 5 or constants.LOCAL_POINTS_2D.index(point) == 7:
                        a.append(self.PSINT_68_main(eta, tau, point[0], point[1]))
                result.append(a)
        return result
    
    def FE_Calc(self, c_list, P_val, ZP_cast, press_axis=2, press_side='max'):
        DxyzDnt = self.DxyzDnt(ZP_cast)
        DEPSIxyzDEnt = self.DEPSIxyzDEnt()
        fe1, fe2, fe3 = [], [], []

        for i in range(8):
            fe1_value = fe2_value = fe3_value = 0.0
            iterator = 0
            for m in c_list:
                for n in c_list:
                    D = DxyzDnt[iterator]
                    PSI = DEPSIxyzDEnt[iterator][i]
                    nx = (D[1][0]*D[2][1] - D[2][0]*D[1][1])
                    ny = (D[2][0]*D[0][1] - D[0][0]*D[2][1])
                    nz = (D[0][0]*D[1][1] - D[1][0]*D[0][1])
                    fe1_value += m * n * P_val * nx * PSI
                    fe2_value += m * n * P_val * ny * PSI
                    fe3_value += m * n * P_val * nz * PSI
                    iterator += 1
            fe1.append(fe1_value)
            fe2.append(fe2_value)
            fe3.append(fe3_value)

        # Визначаємо позиції вузлів грані в залежності від осі та сторони
        val = 1 if press_side == 'max' else -1
        face_indices = [i for i, p in enumerate(constants.LOCAL_NODE_COORDS_3D) if p[press_axis] == val]
        corner = [i for i in face_indices if 0 not in [abs(constants.LOCAL_NODE_COORDS_3D[i][j])
                                                         for j in range(3) if j != press_axis]]
        mid    = [i for i in face_indices if 0     in [abs(constants.LOCAL_NODE_COORDS_3D[i][j])
                                                         for j in range(3) if j != press_axis]]

        Fe = [0.0] * 60
        for k, pos in enumerate(corner):
            Fe[pos]      = fe1[k]
            Fe[pos + 20] = fe2[k]
            Fe[pos + 40] = fe3[k]
        for k, pos in enumerate(mid):
            Fe[pos]      = fe1[k + 4]
            Fe[pos + 20] = fe2[k + 4]
            Fe[pos + 40] = fe3[k + 4]

        return Fe

    def MG_Create(self, All_MGE, AKT_RANGE, All_NT, ZU_cast, AKT_cast):
        """
        Збирає Глобальну Матрицю Жорсткості (MGG) та застосовує граничні умови.
        AKT_RANGE - це загальна кількість вузлів (len(AKT)).
        """
        big_matrix = np.zeros((3 * AKT_RANGE, 3 * AKT_RANGE))

        for index_of_MGE, mge in enumerate(All_MGE):
            for j in range(60):
                for i in range(60):
                    
                    # Визначаємо осі (0=X, 1=Y, 2=Z) та локальний номер вузла
                    if i < 20:
                        xyz_cord_i, i_for_NT = 0, i
                    elif 19 < i < 40:
                        xyz_cord_i, i_for_NT = 1, i - 20
                    else:
                        xyz_cord_i, i_for_NT = 2, i - 40

                    if j < 20:
                        xyz_cord_j, j_for_NT = 0, j
                    elif 19 < j < 40:
                        xyz_cord_j, j_for_NT = 1, j - 20
                    else:
                        xyz_cord_j, j_for_NT = 2, j - 40

                    index_i_for_MG = 3 * All_NT[index_of_MGE][i_for_NT] + xyz_cord_i
                    index_j_for_MG = 3 * All_NT[index_of_MGE][j_for_NT] + xyz_cord_j
                    
                    big_matrix[index_j_for_MG][index_i_for_MG] += mge[j][i]

        for point_coords in ZU_cast:
            if point_coords in AKT_cast:
                index_of_point = AKT_cast.index(point_coords)
                ix = 3 * index_of_point + 0
                iy = 3 * index_of_point + 1
                iz = 3 * index_of_point + 2
                
                penalty_value = 1e16 
                big_matrix[ix][ix] = penalty_value
                big_matrix[iy][iy] = penalty_value
                big_matrix[iz][iz] = penalty_value

        return big_matrix


    def F_Create(self, All_Fe, AKT_RANGE, All_NT):
        """
        Збирає Глобальний Вектор Сил (F).
        """
        big_vector = np.zeros(3 * AKT_RANGE)

        for index_of_FE, fe in enumerate(All_Fe):
            for i in range(60):
                if i < 20:
                    xyz_cord_i, i_for_NT = 0, i
                elif 19 < i < 40:
                    xyz_cord_i, i_for_NT = 1, i - 20
                else:
                    xyz_cord_i, i_for_NT = 2, i - 40

                index_i_for_FE = 3 * All_NT[index_of_FE][i_for_NT] + xyz_cord_i
                big_vector[index_i_for_FE] += fe[i]

        return big_vector

    def calculate_stresses(self, displacements, E, nu, results):
        """
        Обчислює напруження у вузлах через B-матрицю в локальних
        координатах кожного вузла, з усередненням по спільних вузлах.
        """
        G = E / (2 * (1 + nu))
        lam = (E * nu) / ((1 + nu) * (1 - 2 * nu))

        D = np.array([
            [lam+2*G, lam,     lam,     0, 0, 0],
            [lam,     lam+2*G, lam,     0, 0, 0],
            [lam,     lam,     lam+2*G, 0, 0, 0],
            [0,       0,       0,       G, 0, 0],
            [0,       0,       0,       0, G, 0],
            [0,       0,       0,       0, 0, G],
        ])

        num_nodes = len(results.AKT)
        node_stresses = np.zeros((num_nodes, 6))
        node_counts   = np.zeros(num_nodes)

        for el_idx, el_nodes in enumerate(results.NT):
            # координати 20 вузлів цього елемента
            el_coords = [results.AKT[n] for n in el_nodes]

            # переміщення елемента [u0x,u0y,u0z, u1x,u1y,u1z, ...]
            U_e = np.array([
                displacements[3*n + c]
                for n in el_nodes
                for c in range(3)
            ])

            # для кожного вузла — рахуємо B у його власних локальних координатах
            for local_j, global_j in enumerate(el_nodes):
                alpha, beta, gamma = constants.LOCAL_NODE_COORDS_3D[local_j]

                # Якобіан і похідні форм-функцій у цій точці
                J = np.zeros((3, 3))
                dfiabg = []
                for i, lp in enumerate(constants.LOCAL_NODE_COORDS_3D):
                    if i > 7:
                        d = self.DFIABD_center_side(alpha, beta, gamma, lp[0], lp[1], lp[2])
                    else:
                        d = self.DFIABD_angle(alpha, beta, gamma, lp[0], lp[1], lp[2])
                    dfiabg.append(d)
                    x, y, z = el_coords[i]
                    J[0,0]+=x*d[0]; J[0,1]+=y*d[0]; J[0,2]+=z*d[0]
                    J[1,0]+=x*d[1]; J[1,1]+=y*d[1]; J[1,2]+=z*d[1]
                    J[2,0]+=x*d[2]; J[2,1]+=y*d[2]; J[2,2]+=z*d[2]

                try:
                    invJ = np.linalg.inv(J)
                except np.linalg.LinAlgError:
                    continue

                B = np.zeros((6, 60))
                for j in range(20):
                    dg = np.dot(invJ, dfiabg[j])
                    dx, dy, dz = dg
                    idx = 3 * j
                    B[0, idx]     = dx
                    B[1, idx + 1] = dy
                    B[2, idx + 2] = dz
                    B[3, idx]     = dy;  B[3, idx + 1] = dx
                    B[4, idx + 1] = dz;  B[4, idx + 2] = dy
                    B[5, idx]     = dz;  B[5, idx + 2] = dx

                sigma = np.dot(D, np.dot(B, U_e))
                node_stresses[global_j] += sigma
                node_counts[global_j]   += 1

        node_counts[node_counts == 0] = 1
        return (node_stresses / node_counts[:, None]).tolist()

    def calculate_principal_stresses(self, stresses):
            """
            Обчислює головні напруження σ₁ ≥ σ₂ ≥ σ₃ для кожного вузла.

            Метод: власні значення симетричного тензора напружень 3×3.
            Це еквівалентно розв'язку кубічного рівняння (49) з практикуму:
                σ³ - J₁σ² + J₂σ - J₃ = 0
            де J₁, J₂, J₃ — інваріанти тензора напружень.

            :param stresses: список [σx, σy, σz, τxy, τyz, τzx] для кожного вузла
            :return: масив [N × 3] — головні напруження [σ₁, σ₂, σ₃] (спадаючий порядок)
            """
            principal = []
            for s in stresses:
                sx, sy, sz, txy, tyz, tzx = s

                # Будуємо симетричний тензор напружень 3×3
                tensor = np.array([
                    [sx,  txy, tzx],
                    [txy, sy,  tyz],
                    [tzx, tyz, sz ],
                ])

                # Власні значення симетричної матриці
                eigvals = np.linalg.eigvalsh(tensor)

                # Сортуємо у спадаючому порядку: σ₁ ≥ σ₂ ≥ σ₃
                eigvals_sorted = np.sort(eigvals)[::-1]
                principal.append(eigvals_sorted.tolist())

            return principal
    
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