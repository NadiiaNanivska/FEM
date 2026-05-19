from typing import Any
import numpy as np

from task import constants


class ShapeFunctionsMath:
    """
    Весь математичний апарат МСЕ зосереджений тут.

    Порядок застосування (відповідає зведеному алгоритму, заняття 13):
      1. DFIABG_Create()            — передобчислення похідних φᵢ по (α,β,γ) у
                                      27 точках Гауса (формула 39), виконується ОДИН раз.
      2. create_jacobian_for_element()  — матриця Якобі J (3×3) у кожній точці Гауса
                                          (формули 27, 28, 40-41) для КОЖНОГО елемента.
      3. calculate_dfixyz_for_element() — похідні φᵢ по глобальних (x,y,z): J·DFIXYZ=DFIABG
                                          (формула 29, 42), для КОЖНОГО елемента.
      4. calc_MGE()                 — матриця жорсткості елемента 60×60 (формули 15,38,43).
      5. FE_Calc()                  — вектор навантаження елемента 60×1 (формули 44-45).
      6. MG_Create()                — глобальна матриця жорсткості + граничні умови (форм.47).
      7. F_Create()                 — глобальний вектор сил (формула 16).
      8. calculate_stresses()       — напруження σ у вузлах через D·B·u (формула 48).
      9. calculate_principal_stresses() — головні напруження σ₁,σ₂,σ₃ (формула 49).
    """

    def __init__(self):
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 1: Похідні функцій форми у локальних координатах (α,β,γ)
    # Формула (24) практикуму, заняття 4.
    #
    # Функції форми φᵢ(α,β,γ) — квадратичні поліноми. Їхня властивість:
    #   φᵢ(αⱼ,βⱼ,γⱼ) = 1 якщо i=j,  та  0 якщо i≠j
    # Це дозволяє виразити переміщення в будь-якій точці елемента через
    # переміщення у 20 вузлах: u(α,β,γ) = Σ φᵢ(α,β,γ)·uᵢ  (формула 12/25).
    # ─────────────────────────────────────────────────────────────────────────

    def DFIABG_Create(self):
        """
        Передобчислює масив DFIABG[27, 20, 3] — похідні функцій форми
        по локальних координатах у всіх точках Гауса (формула 39, заняття 6).

        DFIABG[k, i, p] = ∂φᵢ/∂ξₚ обчислена в k-тій точці Гауса,
          де ξ₀=α, ξ₁=β, ξ₂=γ.

        Обчислюється ОДИН раз перед циклом по елементах, бо «стандартний»
        елемент [-1,1]³ однаковий для всіх — функції форми не залежать від
        реальної геометрії елемента.

        Порядок точок Гауса: γ змінюється у зовнішньому циклі, α — у внутрішньому
        (27 = 3³ комбінацій трьох рівнів кожної координати).
        """
        result = []
        for gamma in constants.GAUSS_POINTS:
            for beta in constants.GAUSS_POINTS:
                for alpha in constants.GAUSS_POINTS:
                    a = []
                    for i, point in enumerate(constants.LOCAL_NODE_COORDS_3D):
                        # Вузли 1-8 (i=0..7) — кутові, вузли 9-20 (i=8..19) — серединні.
                        # Для кожного типу формула (24) різна — кутові мають ±1 по всіх осях,
                        # серединні мають 0 по одній з осей.
                        if i > 7:
                            a.append(self.DFIABD_center_side(alpha, beta, gamma, point[0], point[1], point[2]))
                        else:
                            a.append(self.DFIABD_angle(alpha, beta, gamma, point[0], point[1], point[2]))
                    result.append(a)
        return result

    def DFIABD_angle(self, alpha, beta, gamma, alpha_i, beta_i, gamma_i):
        """
        Похідні функції форми φᵢ для КУТОВОГО вузла i (вузли 1-8, формула 24).

        Функція форми кутового вузла (перший рядок формули 24):
          φᵢ = (1/8)(1+α·αᵢ)(1+β·βᵢ)(1+γ·γᵢ)(α·αᵢ+β·βᵢ+γ·γᵢ-2)

        Повертає [∂φᵢ/∂α, ∂φᵢ/∂β, ∂φᵢ/∂γ] — вектор із 3 похідних.

        Параметри:
          alpha, beta, gamma   — координата точки Гауса, де обчислюємо похідну
          alpha_i, beta_i, gamma_i — локальні координати вузла i (з LOCAL_NODE_COORDS_3D)
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
        Похідні функції форми φᵢ для СЕРЕДИННОГО вузла i (вузли 9-20, формула 24).
        Серединні вузли мають одну локальну координату = 0 (лежать на середині ребра).

        Повертає [∂φᵢ/∂α, ∂φᵢ/∂β, ∂φᵢ/∂γ].
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

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 2: Матриця Якобі та перехід до глобальних похідних
    # Заняття 4 практикуму, формули 27-29, 40-42.
    # ─────────────────────────────────────────────────────────────────────────

    def create_jacobian_for_element(self, element_coords, dfiabg_matrix):
        """
        Будує 27 матриць Якобі J (по одній на кожну точку Гауса) для одного елемента.

        Матриця Якобі (формула 27) описує зв'язок між локальними і глобальними
        координатами в даній точці:
          J = [ ∂x/∂α  ∂y/∂α  ∂z/∂α ]
              [ ∂x/∂β  ∂y/∂β  ∂z/∂β ]
              [ ∂x/∂γ  ∂y/∂γ  ∂z/∂γ ]

        Елементи J обчислюються через глобальні координати 20 вузлів елемента і похідні φᵢ
        (формула 28):
          ∂x/∂α = Σᵢ xᵢ · ∂φᵢ/∂α

        Фізичний зміст det(J): відношення об'єму реального елемента до об'єму
        «стандартного» куба (об'єм 8). Виступає масштабним коефіцієнтом при
        заміні інтегралів (формула 26).

        Параметри:
          element_coords  — координати 20 вузлів [[x₁,y₁,z₁], ..., [x₂₀,y₂₀,z₂₀]]
          dfiabg_matrix   — DFIABG[27, 20, 3] — похідні φᵢ по локальних коорд.
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
        Обчислює DFIXYZ[27, 20, 3] — похідні функцій форми по ГЛОБАЛЬНИХ координатах.

        Для кожної точки Гауса і кожного вузла розв'язуємо систему (формула 29):
          J · [∂φᵢ/∂x, ∂φᵢ/∂y, ∂φᵢ/∂z]ᵀ = [∂φᵢ/∂α, ∂φᵢ/∂β, ∂φᵢ/∂γ]ᵀ

        Тобто DFIXYZ = J⁻¹ · DFIABG.
        DFIXYZ[27][20][3]
                │   │  └─ три похідні: ∂φ/∂x, ∂φ/∂y, ∂φ/∂z
                │   └─── 20 функцій форми
                └───────── 27 точок Гауса

        Ці похідні потрібні для побудови B-матриці (деформації через переміщення)
        і матриці жорсткості елемента (формула 38).

        DFIXYZ відрізняється від DFIABG: DFIABG — однакові для всіх елементів,
        DFIXYZ — різні для кожного, бо залежать від реальної геометрії (через J).

        Параметри:
          jacobians     — 27 матриць Якобі для поточного елемента
          dfiabg_matrix — DFIABG[27, 20, 3]
        """
        dfixyz_element = []

        for gauss_idx in range(constants.GAUSS_POINTS_COUNT):
            J_matrix = np.array(jacobians[gauss_idx])
            dfixyz_gauss_point = []

            for node_idx in range(constants.NODES_PER_ELEMENT):
                dphi_local = np.array(dfiabg_matrix[gauss_idx][node_idx])

                dphi_global = np.linalg.solve(J_matrix, dphi_local)

                dfixyz_gauss_point.append(dphi_global.tolist())

            dfixyz_element.append(dfixyz_gauss_point)

        return dfixyz_element

    def calculate_determinant(self, a):
        """
        Обчислює визначник матриці Якобі |J| (формула 41).

        |J| — масштабний коефіцієнт при заміні змінних інтегрування.
        Якщо |J| ≤ 0 — сітка некоректна.
        """
        return np.linalg.det(a)

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 3: Матриця жорсткості елемента MGE (60×60)
    # Заняття 6-7 практикуму, формули 15, 38, 43.
    # ─────────────────────────────────────────────────────────────────────────

    def calc_MGE(self, DFIXYZ_cast, determinant_list, c_list, lambda_val, nu_val, mu_val):
        """
        Формує матрицю жорсткості елемента MGE розміром 60×60 (формула 43).

        Розмір 60 = 20 вузлів × 3 координати.

        MGE складається з 6 підматриць 20×20 (формула 15):
          a11, a22, a33 — «прямі» зв'язки (∂/∂x·∂/∂x тощо)
          a12, a13, a23 — «перехресні» зв'язки (∂/∂x·∂/∂y тощо)

        Фіксуємо пару вузлів (i, j):
            ↓
            Рахуємо внесок у 27 точках Гауса → 27 чисел
            ↓
            sum(27 чисел) = один елемент a11[i][j]
            ↓
            Перебираємо всі пари (i=0..19, j=0..19) → матриця 20×20
            ↓
            Робимо так для a11, a22, a33, a12, a13, a23 → 6 матриць 20×20
            ↓
            Збираємо в MGE 60×60

        Кожен коефіцієнт обчислюється квадратурою Гауса (формула 38):
          aᵢⱼ = Σₘ Σₙ Σₖ  cₘcₙcₖ · підінтегральний вираз(m,n,k) · |J(m,n,k)|

        Підінтегральний вираз містить параметри Ламе (заняття 12):
          λ = E·ν / ((1+ν)(1-2ν))  — перший параметр Ламе
          μ = E / (2(1+ν))         — другий параметр Ламе (модуль зсуву G)


        Параметри:
          DFIXYZ_cast    — DFIXYZ[27][20][3] для поточного елемента
          determinant_list — 27 значень |J| (по одному на точку Гауса)
          c_list         — [c₁, c₂, c₃] — ваги Гауса [5/9, 8/9, 5/9]
          lambda_val     — λ·(1+ν)/(E·ν) 
          nu_val         — коефіцієнт Пуассона ν
          mu_val         — μ = E/(2(1+ν))
        """
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

                # Квадратура Гауса: потрійний цикл по 3×3×3=27 точках (формула 38)
                # cₘ, cₙ, cₖ — ваги Гауса; |J| — визначник Якобі в точці
                for m in c_list:
                    for n in c_list:
                        for k in c_list:
                            dfi = DFIXYZ_cast[general_index]

                            # a11: жорсткість X-X (формула 15, a¹¹)
                            a11.append(m * n * k *
                                       (lambda_val * (1 - nu_val) * (dfi[i][0] * dfi[j][0]) +
                                        mu_val * ((dfi[i][1] * dfi[j][1]) + (dfi[i][2] * dfi[j][2]))) *
                                       determinant_list[general_index])

                            # a22: жорсткість Y-Y (формула 15, a²²)
                            a22.append(m * n * k *
                                       (lambda_val * (1 - nu_val) * (dfi[i][1] * dfi[j][1]) +
                                        mu_val * ((dfi[i][0] * dfi[j][0]) + (dfi[i][2] * dfi[j][2]))) *
                                       determinant_list[general_index])

                            # a33: жорсткість Z-Z (формула 15, a³³)
                            a33.append(m * n * k *
                                       (lambda_val * (1 - nu_val) * (dfi[i][2] * dfi[j][2]) +
                                        mu_val * ((dfi[i][0] * dfi[j][0]) + (dfi[i][1] * dfi[j][1]))) *
                                       determinant_list[general_index])

                            # a12: перехресна жорсткість X-Y (формула 15, a¹²)
                            a12.append(m * n * k * (lambda_val * nu_val * (dfi[i][0] * dfi[j][1]) +
                                                    mu_val * (dfi[i][1] * dfi[j][0])) * determinant_list[general_index])

                            # a13: перехресна жорсткість X-Z (формула 15, a¹³)
                            a13.append(m * n * k * (lambda_val * nu_val * (dfi[i][0] * dfi[j][2]) +
                                                    mu_val * (dfi[i][2] * dfi[j][0])) * determinant_list[general_index])

                            # a23: перехресна жорсткість Y-Z (формула 15, a²³)
                            a23.append(m * n * k * (lambda_val * nu_val * (dfi[i][1] * dfi[j][2]) +
                                                    mu_val * (dfi[i][2] * dfi[j][1])) * determinant_list[general_index])

                            general_index += 1

                # Один елемент блоку = зважена сума підінтегральних виразів
                # у всіх 27 точках Гауса для пари вузлів (i, j) у всіх 20 вузлах елемента
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

        # Збираємо повну MGE 60×60 із шести підблоків 20×20.
        # Структура (відображає формулу 11/15):
        #   [ a11 | a12 | a13 ]   [ X-X | X-Y | X-Z ]
        #   [ a21 | a22 | a23 ] = [ Y-X | Y-Y | Y-Z ]
        #   [ a31 | a32 | a33 ]   [ Z-X | Z-Y | Z-Z ]
        # MGE симетрична: a21=a12ᵀ, a31=a13ᵀ, a32=a23ᵀ (практикум, заняття 6)
        matrix1 = np.array(matrix_a11)
        matrix2 = np.array(matrix_a12)
        matrix3 = np.array(matrix_a13)
        matrix4 = np.array(matrix_a22)
        matrix5 = np.array(matrix_a23)
        matrix6 = np.array(matrix_a33)

        big_matrix = np.zeros((60, 60))
        big_matrix[:20, :20]   = matrix1           # X-X
        big_matrix[:20, 20:40] = matrix2           # X-Y
        big_matrix[:20, 40:]   = matrix3           # X-Z
        big_matrix[20:40, :20]   = matrix2.T       # Y-X = (X-Y)ᵀ
        big_matrix[20:40, 20:40] = matrix4         # Y-Y
        big_matrix[20:40, 40:]   = matrix5         # Y-Z
        big_matrix[40:, :20]   = matrix3.T         # Z-X = (X-Z)ᵀ
        big_matrix[40:, 20:40] = matrix5.T         # Z-Y = (Y-Z)ᵀ
        big_matrix[40:, 40:]   = matrix6           # Z-Z

        return big_matrix.tolist()

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 4: Вектор сил від поверхневого тиску (формули 33-36, 44-46)
    # Заняття 5 і 7 практикуму.
    # ─────────────────────────────────────────────────────────────────────────

    def PSINT_angel(self, eta, tau, eta_i, tau_i):
        """
        Часткові похідні функції форми φᵢ по (η, τ) для КУТОВИХ вузлів «стандартного» квадрата
        (формула 33, i=1..4, заняття 5).

        Використовується у DEPSITE() для побудови масиву DPSITE[9, 2, 8]
        (формула 46) — похідних 2D функцій форми на грані елемента.

        """
        result = [
            (1 / 4) * (tau * tau_i + 1) * (eta_i * (eta_i * eta + tau_i * tau - 1) + eta_i * (eta_i * eta + 1)),
            (1 / 4) * (eta_i * eta + 1) * (tau_i * (eta_i * eta + tau_i * tau - 1) + tau_i * (tau_i * tau + 1))
        ]
        return result

    def PSINT_57(self, eta, tau, eta_i, tau_i):
        """
        Часткові похідні φᵢ для СЕРЕДИННИХ вузлів квадрата (вузли 5 та 7, формула 33).
        """
        result = [
            (-tau * tau_i - 1) * eta,
            (1 / 2) * (1 - eta * eta) * tau_i
        ]
        return result

    def PSINT_68(self, eta, tau, eta_i, tau_i):
        """
        Часткові похідні φᵢ для серединних вузлів квадрата де τ_i=0 (вузли 6 та 8, формула 33).
        """
        result = [
            (1 / 2) * (1 - tau * tau) * eta_i,
            (-eta * eta_i - 1) * tau
        ]
        return result

    def PSINT_angel_main(self, eta, tau, eta_i, tau_i):
        """Значення (не похідна) φᵢ для кутових вузлів квадрата (формула 33)."""
        result = (1 / 4) * (tau * tau_i + 1) * (eta * eta_i + 1) * (eta * eta_i + tau_i * tau - 1)
        return result

    def PSINT_57_main(self, eta, tau, eta_i, tau_i):
        """Значення φᵢ для серединних вузлів (вузли 5,7, формула 33)."""
        result = (1 / 2) * (-eta * eta + 1) * (tau_i * tau + 1)
        return result

    def PSINT_68_main(self, eta, tau, eta_i, tau_i):
        """Значення φᵢ для серединних вузлів τ_i=0 (вузли 6,8, формула 33)."""
        result = (1 / 2) * (-tau * tau + 1) * (eta_i * eta + 1)
        return result

    def DEPSITE(self):
        """
        Передобчислює DPSITE[9, 8, 2] — похідні 2D функцій форми по (η,τ)
        у 9 точках Гауса «стандартного» квадрата (формула 46, заняття 7).

        [9]  — 9 точок Гауса (3×3 по η і τ)
            [8]  — 8 вузлів грані кутові (1-4) і серединні (5-8) «стандартного» квадрата (рис. 4).
                [2]  — дві похідні: [∂φᵢ/∂η,  ∂φᵢ/∂τ]

        Використовується у DxyzDnt() для обчислення компонент зовнішньої нормалі
        і, відповідно, вектора навантаження FE.

        DEPSITE()        — похідні 2D функцій форми ∂φ/∂η, ∂φ/∂τ
            ↓
        DxyzDnt()        — дотичні до грані ∂x/∂η, ∂y/∂η ...
            ↓
        FE_Calc()        — нормаль n = дотична × дотична → сила f = P·φ·n
        """
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
        """
        Обчислює похідні глобальних координат (x,y,z) по локальних (η,τ) на грані.

        Відповідає формулі (36) практикуму (заняття 5):
          ∂x/∂η = Σᵢ xᵢ·∂φᵢ/∂η  (перехід від локальних похідних до глобальних)

        Результат — список із 9 матриць [3×2]:
          D[k] = [ [∂x/∂η,  ∂x/∂τ],    ← рядок для x
                   [∂y/∂η,  ∂y/∂τ],    ← рядок для y
                   [∂z/∂η,  ∂z/∂τ] ]   ← рядок для z
            стовп.:   η        τ

        Ці похідні використовуються для обчислення компонент нормалі до грані
        (формула 35), яка потрібна для вектора сил від тиску.

        Параметри:
          xyz — координати 8 вузлів навантаженої грані елемента [[x,y,z], ...]
        """
        result = []
        depsite = self.DEPSITE()
        index_for_depsite = 0
        for _ in constants.GAUSS_POINTS:
            for _ in constants.GAUSS_POINTS:
                summ_x_eta, summ_y_eta, summ_z_eta = [], [], []
                summ_x_tau, summ_y_tau, summ_z_tau = [], [], []
                for index_of_nt, point in enumerate[Any](xyz):
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
        """
        Передобчислює значення (не похідні!) 2D функцій форми φᵢ(η,τ) в:
        [9]  — 9 точках Гауса
            [8]  — значення φᵢ(η,τ) для кожного з 8 вузлів грані

        Використовується у FE_Calc() для обчислення підінтегральних виразів
        вектора навантаження (формула 45).
        """
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
        """
        Формує вектор навантаження елемента FE (розмір 60) від поверхневого тиску P.

        Реалізує формули (44)-(45) практикуму (заняття 7).

        Теорія:
        Тиск P діє нормально до поверхні грані. Вектор сили на вузол i грані:
          fᵢ = ∫∫ P·φᵢ·n dS,
        де n = (nₓ, nᵧ, n_z) — зовнішня нормаль до грані.

        Нормаль обчислюється через векторний добуток дотичних до грані (формула 35):
          nₓ = ∂y/∂η·∂z/∂τ − ∂z/∂η·∂y/∂τ
          nᵧ = ∂z/∂η·∂x/∂τ − ∂x/∂η·∂z/∂τ
          n_z = ∂x/∂η·∂y/∂τ − ∂y/∂η·∂x/∂τ

        Чисельне інтегрування по грані (9 точок Гауса, формула 45):
          fᵢ = Σₘ Σₙ cₘcₙ · P · φᵢ(ηₘ,τₙ) · n(ηₘ,τₙ)

        Повертає вектор FE[60], де ненульові значення лише у 8 вузлах навантаженої
        грані (решта 12 вузлів елемента тиску не відчувають).

        Параметри:
          c_list     — ваги Гауса [c₁, c₂, c₃]
          P_val      — тиск
          ZP_cast    — координати 8 вузлів навантаженої грані
          press_axis — вісь: 0=x, 1=y, 2=z
          press_side — 'max' або 'min' — яка грань навантажена
        """
        DxyzDnt = self.DxyzDnt(ZP_cast)
        DEPSIxyzDEnt = self.DEPSIxyzDEnt()
        fe1, fe2, fe3 = [], [], []

        for i in range(8):
            fe1_value = fe2_value = fe3_value = 0.0
            iterator = 0
            for m in c_list:
                for n in c_list:
                    D = DxyzDnt[iterator]  #  похідні глобальних координат (x,y,z) по локальних (η,τ)
                    PSI = DEPSIxyzDEnt[iterator][i]   # φᵢ в точці Гауса (m,n)

                    # Компоненти нормалі (формула 35)
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

        val = 1 if press_side == 'max' else -1
        face_indices = [i for i, p in enumerate[list[int]](constants.LOCAL_NODE_COORDS_3D) if p[press_axis] == val]
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

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 5: Асемблювання глобальних матриці і вектора
    # Заняття 8 практикуму, формули 47, 17.
    # ─────────────────────────────────────────────────────────────────────────

    def MG_Create(self, All_MGE, AKT_RANGE, All_NT, ZU_cast, AKT_cast):
        """
        Асемблює глобальну матрицю жорсткості MG (3N × 3N) та застосовує
        граничні умови методом штрафних функцій (заняття 10, заняття 8).

        Розмір: 3N, де N — кількість глобальних вузлів.
        Глобальний вектор невідомих (формула 47):
          U = [u¹ₓ, u¹ᵧ, u¹_z, u²ₓ, u²ᵧ, u²_z, ..., u^N_z]

        Тому глобальний індекс для вузла g і компоненти c (0=x,1=y,2=z):
          idx = 3·g + c 

        Локальний індекс i у MGE (0..59) розкодовується так:
          - i < 20   → ось X, локальний вузол i
          - 20≤i<40  → ось Y, локальний вузол i-20
          - 40≤i<60  → ось Z, локальний вузол i-40
        Глобальний вузол = NT[елемент][локальний вузол].

        Граничні умови (заняття 10, спосіб 2 — метод штрафу):
        Для кожного закріпленого вузла (ZU) ставимо на діагональ MG велике число
        PENALTY = 1e16. Це змушує розв'язок прагнути до нуля без зміни розміру системи.

        Параметри:
          All_MGE   — список матриць жорсткості елементів [M × 60 × 60]
          AKT_RANGE — N (кількість глобальних вузлів)
          All_NT    — матриця зв'язності NT [M × 20]
          ZU_cast   — координати закріплених вузлів (формула 30)
          AKT_cast  — список координат усіх вузлів
        """
        big_matrix = np.zeros((3 * AKT_RANGE, 3 * AKT_RANGE))

        for index_of_MGE, mge in enumerate(All_MGE):
            for j in range(60):
                for i in range(60):
                    # Розкодовуємо локальний індекс → (вісь, номер вузла в елементі)
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

                    # Глобальні індекси у MG (формула 47)
                    index_i_for_MG = 3 * All_NT[index_of_MGE][i_for_NT] + xyz_cord_i
                    index_j_for_MG = 3 * All_NT[index_of_MGE][j_for_NT] + xyz_cord_j

                    # Підсумовуємо внески від усіх елементів — спільні вузли
                    # сусідніх елементів дають суму їхніх жорсткостей (заняття 8)
                    big_matrix[index_j_for_MG][index_i_for_MG] += mge[j][i]

        # Граничні умови: метод штрафних функцій (заняття 10, спосіб 2)
        # Для закріпленого вузла MG[idx,idx] = 1e16 >> інші коефіцієнти рядка
        # → розв'язок u → 0 автоматично
        for point_coords in ZU_cast:
            if point_coords in AKT_cast:
                index_of_point = AKT_cast.index(point_coords)
                ix = 3 * index_of_point
                iy = 3 * index_of_point + 1
                iz = 3 * index_of_point + 2

                penalty_value = constants.PENALTY_VALUE
                big_matrix[ix][ix] = penalty_value
                big_matrix[iy][iy] = penalty_value
                big_matrix[iz][iz] = penalty_value

        return big_matrix 

    def F_Create(self, All_Fe, AKT_RANGE, All_NT):
        """
        Асемблює глобальний вектор зовнішніх сил F (розмір 3N).

        Принцип аналогічний MG_Create: кожен елементний вектор FE[60]
        розсилається по глобальному вектору F за допомогою NT.

        F[3·g + c] += FE_елемента[локальний_індекс]

        Якщо вузол входить у декілька навантажених граней — сили підсумовуються.

        Параметри:
          All_Fe    — список векторів навантаження елементів [M × 60]
          AKT_RANGE — N (кількість глобальних вузлів)
          All_NT    — NT [M × 20]
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

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 6: Розрахунок напружень
    # Заняття 12 практикуму, формули 48, 49.
    # ─────────────────────────────────────────────────────────────────────────

    def calculate_stresses(self, displacements, E, nu, results):
        """
        Обчислює компоненти тензора напружень σ у кожному вузлі (формула 48).

        Алгоритм (заняття 12):
        1. Для кожного елемента та кожного його вузла:
           a) Обчислюємо Якобі і DFIXYZ у локальній точці вузла.
           b) Будуємо B-матрицю (6×60):
              B пов'язує переміщення вузлів елемента з деформаціями:
              ε = B·uᵉ
           c) Напруження: σ = D·ε = D·B·uᵉ
        2. Якщо вузол входить у декілька елементів — усереднюємо результати.

        D-матриця (6×6) — матриця констант (закон Гука, формула 2 практикуму):

          D = λ · [ (1-ν)      ν         ν       0           0           0        ]
                  [  ν        (1-ν)       ν       0           0           0        ]
                  [  ν         ν        (1-ν)     0           0           0        ]
                  [  0         0          0    (1-2ν)/2       0           0        ]
                  [  0         0          0       0        (1-2ν)/2       0        ]
                  [  0         0          0       0           0        (1-2ν)/2    ]

        де λ = E / ((1+ν)(1-2ν)) — параметр Ламе практикуму (формула 6).
        Напруження: формула 2 практикуму.

        B-матриця (6×60) — містить часткові похідні функцій форми у глобальних
        координатах (∂φⱼ/∂x, ∂φⱼ/∂y, ∂φⱼ/∂z) для кожного з 20 вузлів елемента.

        B =  [ ∂φ/∂x    0       0    | для кожного з 20 вузлів ]
               [ 0      ∂φ/∂y    0    |                          ]
               [ 0        0    ∂φ/∂z  |                          ]
               [ ∂φ/∂y  ∂φ/∂x    0    |                          ]
               [ 0      ∂φ/∂z  ∂φ/∂y  |                          ]
               [ ∂φ/∂z    0    ∂φ/∂x  |                          ]

        Похідна переміщення — це сума добутків переміщення кожного вузла на
        часткову похідну його функції форми (формула 48 практикуму):
          ∂ux/∂x = Σⱼ uⱼx · ∂φⱼ/∂x  ← перший рядок B · uᵉ
          ∂uz/∂x = Σⱼ uⱼz · ∂φⱼ/∂x  ← доданок у γzx

        Множення D · B · uᵉ відтворює формули практикуму (2),
        де B·uᵉ дає вектор деформацій ε, а D·ε — вектор напружень σ.

        Повертає список [N × 6]: [σx, σy, σz, τxy, τyz, τzx] для кожного вузла.
        """
        lam = E / ((1 + nu) * (1 - 2 * nu))
        mu = (1 - 2 * nu) / 2 
        D = lam * np.array([
            [1-nu,  nu,   nu,   0,  0,  0],
            [nu,    1-nu, nu,   0,  0,  0],
            [nu,    nu,   1-nu, 0,  0,  0],
            [0,     0,    0,    mu, 0,  0],
            [0,     0,    0,    0,  mu, 0],
            [0,     0,    0,    0,  0,  mu],
        ])

        num_nodes = len(results.AKT)
        node_stresses = np.zeros((num_nodes, 6))
        node_counts   = np.zeros(num_nodes)

        for el_idx, el_nodes in enumerate(results.NT):
            el_coords = [results.AKT[n] for n in el_nodes]

            U_e = np.array([
                displacements[3*n + c]
                for n in el_nodes
                for c in range(3)
            ])

            # Для кожного вузла обчислюємо B у локальних координатах самого вузла
            for local_j, global_j in enumerate(el_nodes):
                alpha, beta, gamma = constants.LOCAL_NODE_COORDS_3D[local_j]

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

                # B-матриця (6×60):
                # Кожен вузол j займає стовпці [3j, 3j+1, 3j+2]
                B = np.zeros((6, 60))
                for j in range(20):
                    dg = np.dot(invJ, dfiabg[j])   # DFIXYZ = J⁻¹ · DFIABG
                    dx, dy, dz = dg
                    idx = 3 * j
                    B[0, idx]     = dx           
                    B[1, idx + 1] = dy             
                    B[2, idx + 2] = dz         
                    B[3, idx]     = dy;  B[3, idx + 1] = dx 
                    B[4, idx + 1] = dz;  B[4, idx + 2] = dy
                    B[5, idx]     = dz;  B[5, idx + 2] = dx  

                # σ = D · B · uᵉ  (формула 48)
                sigma = np.dot(D, np.dot(B, U_e))
                node_stresses[global_j] += sigma
                node_counts[global_j]   += 1

        # Усереднення: вузол може належати до 8 елементів одночасно
        node_counts[node_counts == 0] = 1
        return (node_stresses / node_counts[:, None]).tolist()  # N×6: [σx,σy,σz,τxy,τyz,τzx]

    def calculate_principal_stresses(self, stresses):
        """
        Обчислює головні напруження σ₁ ≥ σ₂ ≥ σ₃ для кожного вузла (формула 49).

        У кожній точці тіла є три взаємно перпендикулярні напрямки, у
        яких внутрішні зусилля є екстремальними, а, отже, й найбільш
        небезпечними (через що вони називаються головними напруженнями). 
        Ці головні напруження — є власними значеннями тензора напружень 3×3:

          | σx   τxy  τzx |
          | τxy  σy   τyz |
          | τzx  τyz  σz  |

        Це еквівалентно кубічному рівнянню (49) практикуму:
          σ³ − J₁·σ² + J₂·σ − J₃ = 0 - характеристичне рівняння матриці тензора
        де J₁ = σx+σy+σz, J₂, J₃ — інваріанти тензора.

        Головні напруження важливі для аналізу міцності конструкцій: саме вони
        визначають небезпечні точки (де σ₁ максимальне або σ₃ найбільш стискаюче).

        Параметри:
          stresses — список [σx, σy, σz, τxy, τyz, τzx] для кожного вузла

        Повертає: список [N × 3] — [σ₁, σ₂, σ₃] у спадаючому порядку.
        """
        principal = []
        for s in stresses:
            sx, sy, sz, txy, tyz, tzx = s

            # Симетричний тензор напружень 3×3
            tensor = np.array([
                [sx,  txy, tzx],
                [txy, sy,  tyz],
                [tzx, tyz, sz ],
            ])

            # Власні значення симетричної матриці
            eigvals = np.linalg.eigvalsh(tensor)

            # Сортуємо σ₁ ≥ σ₂ ≥ σ₃
            eigvals_sorted = np.sort(eigvals)[::-1]
            principal.append(eigvals_sorted.tolist())

        return principal  # N×3: [σ₁, σ₂, σ₃] для кожного вузла

    # ─────────────────────────────────────────────────────────────────────────
    # БЛОК 7: Допоміжні функції
    # ─────────────────────────────────────────────────────────────────────────

    def save_dfiabg_to_txt(self, dfiabg_matrix, filename="statics/DFIABG.txt"):
        """
        Зберігає DFIABG[27, 20, 3] у текстовий файл для перевірки обчислень.
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
        Зберігає DFIXYZ[27, 20, 3] для одного елемента у текстовий файл.
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


def compute_vm(s):
    """
    Обчислює еквівалентне напруження Мізеса σ_VM для масиву вузлів.
    """
    sx, sy, sz, txy, tyz, tzx = s[:,0], s[:,1], s[:,2], s[:,3], s[:,4], s[:,5]
    return np.sqrt(0.5*((sx-sy)**2 + (sy-sz)**2 + (sz-sx)**2
                        + 6*(txy**2 + tyz**2 + tzx**2)))
