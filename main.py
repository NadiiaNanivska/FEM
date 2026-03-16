import math

import numpy as np
import wx
import plotly.graph_objects as go
from wx.lib.masked import NumCtrl


class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Створення полів введення
        self.a_entry = wx.TextCtrl(self)
        self.b_entry = wx.TextCtrl(self)
        self.c_entry = wx.TextCtrl(self)

        self.n_A = wx.TextCtrl(self)
        self.n_B = wx.TextCtrl(self)
        self.n_C = wx.TextCtrl(self)

        self.E_entry = wx.TextCtrl(self)
        self.nu_entry = wx.TextCtrl(self)
        self.P_entry = wx.TextCtrl(self)

        self.presurre = wx.TextCtrl(self)

        self.all_points_button = wx.Button(self, label="Calculate")
        self.all_points_button.Bind(wx.EVT_BUTTON, self.on_all_points_button)

        # Розташування елементів на панелі
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(self, label="n_A:"), 0, wx.ALL, 5)
        sizer.Add(self.n_A, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="n_B:"), 0, wx.ALL, 5)
        sizer.Add(self.n_B, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="n_C:"), 0, wx.ALL, 5)
        sizer.Add(self.n_C, 0, wx.ALL, 5)

        sizer.Add(wx.StaticText(self, label="A:"), 0, wx.ALL, 5)
        sizer.Add(self.a_entry, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="B:"), 0, wx.ALL, 5)
        sizer.Add(self.b_entry, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="C:"), 0, wx.ALL, 5)
        sizer.Add(self.c_entry, 0, wx.ALL, 5)

        sizer.Add(wx.StaticText(self, label="Side for pressure:"), 0, wx.ALL, 5)
        sizer.Add(self.presurre, 0, wx.ALL, 5)

        sizer.Add(wx.StaticText(self, label="E:"), 0, wx.ALL, 5)
        sizer.Add(self.E_entry, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="nu:"), 0, wx.ALL, 5)
        sizer.Add(self.nu_entry, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label="P:"), 0, wx.ALL, 5)
        sizer.Add(self.P_entry, 0, wx.ALL, 5)

        sizer.Add(self.all_points_button, 0, wx.ALL, 5)

        self.SetSizer(sizer)

    def create_points(self, a, b, c, na, nb, nc):

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
        a_size = a_end - a_start
        b_size = b_end - b_start
        c_size = c_end - c_start

        x = [a_start,  # 1
             a_end,  # 2
             a_end,  # 3
             a_start,  # 4
             a_start,  # 5
             a_end,  # 6
             a_end,  # 7
             a_start,  # 8
             a_start + a_size / 2,  # 9
             a_end,  # 10
             a_start + a_size / 2,  # 11
             a_start,  # 12
             a_start,  # 13
             a_end,  # 14
             a_end,  # 15
             a_start,  # 16
             a_start + a_size / 2,  # 17
             a_end,  # 18
             a_start + a_size / 2,  # 19
             a_start  # 20
             ]
        y = [b_start,  # 1
             b_start,  # 2
             b_end,  # 3
             b_end,  # 4
             b_start,  # 5
             b_start,  # 6
             b_end,  # 7
             b_end,  # 8
             b_start,  # 9
             b_start + b_size / 2,  # 10
             b_end,  # 11
             b_start + b_size / 2,  # 12
             b_start,  # 13
             b_start,  # 14
             b_end,  # 15
             b_end,  # 16
             b_start,  # 17
             b_start + b_size / 2,  # 18
             b_end,  # 19
             b_start + b_size / 2  # 20
             ]
        z = [c_start,  # 1
             c_start,  # 2
             c_start,  # 3
             c_start,  # 4
             c_end,  # 5
             c_end,  # 6
             c_end,  # 7
             c_end,  # 8
             c_start,  # 9
             c_start,  # 10
             c_start,  # 11
             c_start,  # 12
             c_start + c_size / 2,  # 13
             c_start + c_size / 2,  # 14
             c_start + c_size / 2,  # 15
             c_start + c_size / 2,  # 16
             c_end,  # 17
             c_end,  # 18
             c_end,  # 19
             c_end  # 20
             ]
        result = []
        for i in range(20):
            result.append([x[i], y[i], z[i]])
        return result

    def separate_point(self, a, b, c, na, nb, nc):
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

    def NT_transform(self, akt, elem):
        result = []
        for cube in elem:
            nt_cube = []
            for i in cube:
                nt_cube.append(akt.index(i))
            result.append(nt_cube)
        return result

    def ZU_Chose(self, eleme):
        minim = min([sublist[2] for sublist in eleme])
        return [sublist for sublist in eleme if sublist[2] == minim]

    def ZP_Chose(self, eleme, side, side_of_axis):
        result = []
        if side == 1 or side == 3 or side == 5:
            minim = min([sublist[side_of_axis] for sublist in eleme])
            result = [sublist for sublist in eleme if sublist[side_of_axis] == minim]
        elif side == 2 or side == 4 or side == 6:
            maxim = max([sublist[side_of_axis] for sublist in eleme])
            result = [sublist for sublist in eleme if sublist[side_of_axis] == maxim]
        return result

    def DFIABG_Create(self):
        result = []
        for gamma in gamma_for:
            for beta in beta_for:
                for alpha in alpha_for:
                    a = []
                    for point in local_points:
                        if local_points.index(point) > 7:
                            a.append(self.DFIABD_center_side(alpha, beta, gamma, point[0], point[1], point[2]))
                        else:
                            a.append(self.DFIABD_angle(alpha, beta, gamma, point[0], point[1], point[2]))
                    result.append(a)
        return result

    def DFIABD_angle(self, alpha, beta, gamma, alpha_i, beta_i, gamma_i):
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

    def DJ_Create(self, xyz):
        result = self.DExyzDEabg(xyz)
        return result

    def DELTA(self, xyz, alpha, beta, gamma):
        result = [
            self.DxyzDabg(xyz, alpha, beta, gamma, 0),
            self.DxyzDabg(xyz, alpha, beta, gamma, 1),
            self.DxyzDabg(xyz, alpha, beta, gamma, 2)
        ]
        return result

    def DExyzDEabg(self, xyz):
        result = []
        dfiabj = self.DFIABG_Create()
        for i in range(27):
            summ_x_a = []
            summ_x_b = []
            summ_x_g = []
            summ_y_a = []
            summ_y_b = []
            summ_y_g = []
            summ_z_a = []
            summ_z_b = []
            summ_z_g = []
            for point in xyz:
                index_of_nt = xyz.index(point)
                summ_x_a.append(point[0] * dfiabj[i][index_of_nt][0])
                summ_x_b.append(point[0] * dfiabj[i][index_of_nt][1])
                summ_x_g.append(point[0] * dfiabj[i][index_of_nt][2])

                summ_y_a.append(point[1] * dfiabj[i][index_of_nt][0])
                summ_y_b.append(point[1] * dfiabj[i][index_of_nt][1])
                summ_y_g.append(point[1] * dfiabj[i][index_of_nt][2])

                summ_z_a.append(point[2] * dfiabj[i][index_of_nt][0])
                summ_z_b.append(point[2] * dfiabj[i][index_of_nt][1])
                summ_z_g.append(point[2] * dfiabj[i][index_of_nt][2])
            result.append([
                [sum(summ_x_a), sum(summ_y_a), sum(summ_z_a)],
                [sum(summ_x_b), sum(summ_y_b), sum(summ_z_b)],
                [sum(summ_x_g), sum(summ_y_g), sum(summ_z_g)],
            ])

        return result

    def DxyzDabg(self, xyz, alpha, beta, gamma, index_of_abg):
        summ_x = 0
        summ_y = 0
        summ_z = 0
        for i in range(len(xyz)):
            if i > 7:
                centr_item = self.DFIABD_center_side(alpha, beta, gamma, local_points[i][0], local_points[i][1],
                                                     local_points[i][2])
                summ_x += xyz[i][0] * centr_item[index_of_abg]
                summ_y += xyz[i][1] * centr_item[index_of_abg]
                summ_z += xyz[i][2] * centr_item[index_of_abg]
            else:
                side_Item = self.DFIABD_angle(alpha, beta, gamma, local_points[i][0], local_points[i][1],
                                              local_points[i][2])
                summ_x += xyz[i][0] * side_Item[index_of_abg]
                summ_y += xyz[i][1] * side_Item[index_of_abg]
                summ_z += xyz[i][2] * side_Item[index_of_abg]

        return [summ_x, summ_y, summ_z]

    def calculate_determinant(self, a):
        det = a[0][0] * a[1][1] * a[2][2] + a[0][1] * a[1][2] * a[2][0] + a[0][2] * a[1][0] * a[2][1] - a[0][2] * a[1][
            1] * a[2][0] - a[0][0] * a[1][2] * a[2][1] - a[0][1] * a[1][0] * a[2][2]
        return det

    def solve_linear_equation(self, A, b):
        x = np.linalg.solve(A, b).tolist()
        return x

    def Solv_SLAR_for_elements(self, elements_cast, DJ_cast, DFIABG_cast):
        result = []
        for i in range(len(elements_cast)):
            result.append(self.Solv_SLAR_for_element(DJ_cast[i], DFIABG_cast))
        return result

    def Solv_SLAR_for_element(self, DJacobian, DFIABG_cast):
        result = []
        for delta_item in range(len(DJacobian)):
            dfixyz = []
            for points in DFIABG_cast[delta_item]:
                solved_L_E = self.solve_linear_equation(DJacobian[delta_item], points)
                dfixyz.append(solved_L_E)
            result.append(dfixyz)
        return result

    def calc_MGE(self, DFIXYZ_cast, determinant_list, c_list, lambda_val, nu_val, mu_val):
        matrix_a11 = []
        matrix_a22 = []
        matrix_a33 = []
        matrix_a12 = []
        matrix_a13 = []
        matrix_a23 = []
        for i in range(20):
            line_of_matrix_a11 = []
            line_of_matrix_a22 = []
            line_of_matrix_a33 = []
            line_of_matrix_a12 = []
            line_of_matrix_a13 = []
            line_of_matrix_a23 = []
            for j in range(20):
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
        for eta in eta_for:
            for tau in tau_for:
                a = []
                for point in local_2d_points:
                    if local_2d_points.index(point) < 4:
                        a.append(self.PSINT_angel(eta, tau, point[0], point[1]))
                    elif local_2d_points.index(point) == 4 or local_2d_points.index(point) == 6:
                        a.append(self.PSINT_57(eta, tau, point[0], point[1]))
                    elif local_2d_points.index(point) == 5 or local_2d_points.index(point) == 7:
                        a.append(self.PSINT_68(eta, tau, point[0], point[1]))
                result.append(a)
        return result

    def DxyzDnt(self, xyz):
        result = []
        depsite = self.DEPSITE()
        index_for_depsite = 0
        for eta in eta_for:
            for tau in tau_for:
                summ_x_eta = []
                summ_y_eta = []
                summ_z_eta = []
                summ_x_tau = []
                summ_y_tau = []
                summ_z_tau = []
                for point in xyz:
                    index_of_nt = xyz.index(point)
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
        for eta in eta_for:
            for tau in tau_for:
                a = []
                for point in local_2d_points:
                    if local_2d_points.index(point) < 4:
                        a.append(self.PSINT_angel_main(eta, tau, point[0], point[1]))
                    elif local_2d_points.index(point) == 4 or local_2d_points.index(point) == 6:
                        a.append(self.PSINT_57_main(eta, tau, point[0], point[1]))
                    elif local_2d_points.index(point) == 5 or local_2d_points.index(point) == 7:
                        a.append(self.PSINT_68_main(eta, tau, point[0], point[1]))
                result.append(a)
        return result

    def FE_Calc(self, c_list, P_val, ZP_cast):
        DxyzDnt = self.DxyzDnt(ZP_cast)
        DEPSIxyzDEnt = self.DEPSIxyzDEnt()
        fe1 = []
        fe2 = []
        fe3 = []
        for i in range(8):  # [-1, -1]
            fe1_value = 0
            fe2_value = 0
            fe3_value = 0
            iterator_for_help = 0
            for m in c_list:
                for n in c_list:
                    DxyzDnt_item = DxyzDnt[iterator_for_help]
                    DEPSIxyzDEnt_item = DEPSIxyzDEnt[iterator_for_help][i]
                    fe1_value += m * n * P_val * (
                            DxyzDnt_item[1][0] * DxyzDnt_item[2][1] - DxyzDnt_item[2][0] * DxyzDnt_item[1][1]) \
                                 * DEPSIxyzDEnt_item
                    fe2_value += m * n * P_val * (
                            DxyzDnt_item[2][0] * DxyzDnt_item[0][1] - DxyzDnt_item[0][0] * DxyzDnt_item[2][1]) \
                                 * DEPSIxyzDEnt_item
                    fe3_value += m * n * P_val * (
                            DxyzDnt_item[0][0] * DxyzDnt_item[1][1] - DxyzDnt_item[1][0] * DxyzDnt_item[0][1]) \
                                 * DEPSIxyzDEnt_item
                    iterator_for_help += 1
            fe1.append(fe1_value)
            fe2.append(fe2_value)
            fe3.append(fe3_value)

        # Створюємо масив Fe розміром 60 і заповнюємо його нулями
        Fe = [0, 0, 0, 0, fe1[0], fe1[1], fe1[2], fe1[3], 0, 0,
              0, 0, 0, 0, 0, 0, fe1[4], fe1[5], fe1[6], fe1[7],
              0, 0, 0, 0, fe2[0], fe2[1], fe2[2], fe2[3], 0, 0,
              0, 0, 0, 0, 0, 0, fe2[4], fe2[5], fe2[6], fe2[7],
              0, 0, 0, 0, fe3[0], fe3[1], fe3[2], fe3[3], 0, 0,
              0, 0, 0, 0, 0, 0, fe3[4], fe3[5], fe3[6], fe3[7]]

        return Fe

    def MG_Create(self, All_MGE, AKT_RANGE, All_NT, ZU_cast,AKT_cast):
        big_matrix = np.zeros((3 * AKT_RANGE, 3 * AKT_RANGE))
        result = big_matrix.tolist()

        for mge in All_MGE:
            index_of_MGE = All_MGE.index(mge)
            for j in range(60):
                for i in range(60):

                    if i < 20:
                        xyz_cord_i = 0
                        i_for_NT = i
                    elif 19 < i < 40:
                        xyz_cord_i = 1
                        i_for_NT = i - 20
                    else:
                        xyz_cord_i = 2
                        i_for_NT = i - 40

                    if j < 20:
                        xyz_cord_j = 0
                        j_for_NT = j
                    elif 19 < j < 40:
                        xyz_cord_j = 1
                        j_for_NT = j - 20
                    else:
                        xyz_cord_j = 2
                        j_for_NT = j - 40

                    index_i_for_MG = 3 * All_NT[index_of_MGE][i_for_NT] + xyz_cord_i
                    index_j_for_MG = 3 * All_NT[index_of_MGE][j_for_NT] + xyz_cord_j
                    result[index_j_for_MG][index_i_for_MG] += mge[j][i]

        for i in ZU_cast:
            index_of_point = AKT_cast.index(i)
            ix = 3 * index_of_point + 0
            iy = 3 * index_of_point + 1
            iz = 3 * index_of_point + 2
            result[ix][ix] = 10000000000000000
            result[iy][iy] = 10000000000000000
            result[iz][iz] = 10000000000000000

        return result

    def F_Create(self, All_Fe, AKT_RANGE, All_NT):
        big_matrix = np.zeros((3 * AKT_RANGE))
        result = big_matrix.tolist()
        for fe in All_Fe:
            index_of_FE = All_Fe.index(fe)
            for i in range(60):

                if i < 20:
                    xyz_cord_i = 0
                    i_for_NT = i
                elif 19 < i < 40:
                    xyz_cord_i = 1
                    i_for_NT = i - 20
                else:
                    xyz_cord_i = 2
                    i_for_NT = i - 40

                index_i_for_FE = 3 * All_NT[index_of_FE][i_for_NT] + xyz_cord_i
                result[index_i_for_FE] += fe[i]
        return result

    def on_all_points_button(self, event):
        preasure = []
        FE = []
        F = []
        MG = []
        c_1 = 5 / 9
        c_2 = 8 / 9
        c_3 = 5 / 9

        E = 0
        nu = 0
        P = 0
        liambda = 0
        mu = 0

        # Отримання значень з полів введення (з дефолтними значеннями)
        try:
            a_val = float(self.a_entry.GetValue()) if self.a_entry.GetValue() != '' else 2.0
            b_val = float(self.b_entry.GetValue()) if self.b_entry.GetValue() != '' else 2.0
            c_val = float(self.c_entry.GetValue()) if self.c_entry.GetValue() != '' else 10.0
            na_val = int(self.n_A.GetValue()) if self.n_A.GetValue() != '' else 2
            nb_val = int(self.n_B.GetValue()) if self.n_B.GetValue() != '' else 2
            nc_val = int(self.n_C.GetValue()) if self.n_C.GetValue() != '' else 3
            E = float(self.E_entry.GetValue()) if self.E_entry.GetValue() != '' else 10000.0
            nu = float(self.nu_entry.GetValue()) if self.nu_entry.GetValue() != '' else 0.48
            P = float(self.P_entry.GetValue()) if self.P_entry.GetValue() != '' else 5000.0
            temp = self.presurre.GetValue()
            if temp != '':
                for i in temp.split(','):
                    preasure.append(int(i) - 1)
        except ValueError:
            wx.MessageBox("Перевірте правильність вводу даних!", "Помилка", wx.OK | wx.ICON_ERROR)
            return

        liambda = E / ((1 + nu) * (1 - 2 * nu))
        mu = E / (2 * (1 + nu))

        # --- РОЗРАХУНКОВА ЧАСТИНА ---
        elements = self.create_points(a_val, b_val, c_val, na_val, nb_val, nc_val)
        AKT = self.separate_point(a_val, b_val, c_val, na_val, nb_val, nc_val)
        NT = self.NT_transform(AKT, elements)
        ZP = []
        ZU = self.ZU_Chose(AKT)
        DFIABG = self.DFIABG_Create()
        
        DJ = []
        for i in elements:
            DJ.append(self.DJ_Create(i))

        DJ_det = []
        for DJ_for_one in DJ:
            DJ_det_for_one = []
            for i in DJ_for_one:
                DJ_det_for_one.append(self.calculate_determinant(i))
            DJ_det.append(DJ_det_for_one)

        DFIXYZ = self.Solv_SLAR_for_elements(elements, DJ, DFIABG)

        list_of_MGE = []
        for i in range(len(elements)):
            list_of_MGE.append(
                self.calc_MGE(DFIXYZ[i], DJ_det[i], [c_1, c_2, c_3], liambda, nu, mu))

        if len(preasure) == 0:
            for i in range(na_val * nb_val):
                all_el = len(elements) - 1
                ZP.append(self.ZP_Chose(elements[all_el - i], 6, 2))
            for i in range(len(NT) - len(ZP)):
                FE.append(np.zeros(60).tolist())
            for i in ZP:
                FE.append(self.FE_Calc([c_1, c_2, c_3], P, i))
        else:
            for i in preasure:
                ZP.append(self.ZP_Chose(elements[i], 6, 2))
            zp_index = 0
            for i in range(len(elements)):
                if i in preasure:
                    FE.append(self.FE_Calc([c_1, c_2, c_3], P, ZP[zp_index]))
                    zp_index += 1
                else:
                    FE.append(np.zeros(60).tolist())

        MG = self.MG_Create(list_of_MGE, len(AKT), NT, ZU, AKT)
        F = self.F_Create(FE, len(AKT), NT)
        
        # Розв'язок системи
        result_points = self.solve_linear_equation(MG, F)

        # Розрахунок напружень (доданий раніше)
        print("Calculating Stresses...")
        stresses = self.calculate_stresses(result_points, elements, AKT, NT, E, nu)
        print("Stresses calculated.")

        # --- ПІДГОТОВКА КООРДИНАТ ---
        x_points = [sublist[0] for sublist in AKT]
        y_points = [sublist[1] for sublist in AKT]
        z_points = [sublist[2] for sublist in AKT]

        # Деформовані координати
        x_points_modified = np.zeros(len(AKT)).tolist()
        y_points_modified = np.zeros(len(AKT)).tolist()
        z_points_modified = np.zeros(len(AKT)).tolist()
        
        # Масштаб деформації (автоматично 1.0, можна змінити для візуалізації)
        scale_factor = 1.0 

        for i in range(len(result_points)):
            j = i // 3
            if (i + 1) % 3 == 1:
                x_points_modified[j] = x_points[j] + result_points[i] * scale_factor
            if (i + 1) % 3 == 2:
                y_points_modified[j] = y_points[j] + result_points[i] * scale_factor
            if (i + 1) % 3 == 0:
                z_points_modified[j] = z_points[j] + result_points[i] * scale_factor

        # --- ВІЗУАЛІЗАЦІЯ (PLOTLY) ---
        fig = go.Figure()

        # 1. Додаємо початкові вузли (Червоні точки)
        node_numbers = [str(i) for i in range(len(x_points))]
        
        fig.add_trace(go.Scatter3d(
            x=x_points, y=y_points, z=z_points,
            mode='markers+text',    
            name='Початкова форма',
            marker=dict(size=4, color='red', opacity=0.8),
            text=node_numbers,
            textposition="top center",
            textfont=dict(size=9, color='darkred'),
            hoverinfo='x+y+z' 
        ))

        # 2. Додаємо деформовані вузли (Зелені точки)
        # Формуємо текст з напруженнями для наведення
        hover_text_def = []
        for i in range(len(z_points_modified)):
            s = stresses[i]
            # Виводимо Sigma_ZZ та Sigma_VonMises (приблизно) для інфо
            txt = (f"Node {i}<br>"
                   f"Sz: {s[2]:.2e}<br>" # Sigma ZZ
                   f"Sx: {s[0]:.2e}<br>"
                   f"Sy: {s[1]:.2e}")
            hover_text_def.append(txt)

        fig.add_trace(go.Scatter3d(
            x=x_points_modified, y=y_points_modified, z=z_points_modified,
            mode='markers',
            name='Деформована форма',
            marker=dict(size=4, color='green', opacity=0.8),
            text=hover_text_def,
            hoverinfo='text+x+y+z'
        ))

        # 3. Побудова ліній (Wireframe)
        # Оптимізація: збираємо всі координати ліній в один список, розділяючи None
        # Це значно швидше, ніж додавати тисячі окремих ліній
        def build_wireframe_coords(nodes_x, nodes_y, nodes_z, nt_list):
            x_lines, y_lines, z_lines = [], [], []
            # Пари індексів, що утворюють ребра куба (20-вузлового)
            # Спростимо до основних ребер для візуалізації (кутові точки)
            # Кутові індекси в NT: 0, 1, 2, 3 (низ), 4, 5, 6, 7 (верх)
            edges = [
                (0,1), (1,2), (2,3), (3,0), # Низ
                (4,5), (5,6), (6,7), (7,4), # Верх
                (0,4), (1,5), (2,6), (3,7)  # Стійки
            ]
            
            for el_nt in nt_list:
                for p1, p2 in edges:
                    idx1, idx2 = el_nt[p1], el_nt[p2]
                    x_lines.extend([nodes_x[idx1], nodes_x[idx2], None])
                    y_lines.extend([nodes_y[idx1], nodes_y[idx2], None])
                    z_lines.extend([nodes_z[idx1], nodes_z[idx2], None])
            return x_lines, y_lines, z_lines

        # Лінії для початкової форми (Сині напівпрозорі)
        lx, ly, lz = build_wireframe_coords(x_points, y_points, z_points, NT)
        fig.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz,
            mode='lines',
            name='Сітка (До)',
            line=dict(color='blue', width=2),
            opacity=0.3,
            hoverinfo='skip'
        ))

        # Лінії для деформованої форми (Зелені)
        lx_mod, ly_mod, lz_mod = build_wireframe_coords(x_points_modified, y_points_modified, z_points_modified, NT)
        fig.add_trace(go.Scatter3d(
            x=lx_mod, y=ly_mod, z=lz_mod,
            mode='lines',
            name='Сітка (Після)',
            line=dict(color='lime', width=3),
            hoverinfo='skip'
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
            title=f"Деформація (P={P:.0e}, E={E:.0e})",
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

        # Відкриває графік у браузері
        # Створення імені файлу (можна додати шлях, якщо потрібно)
        import os
        output_file = os.path.abspath("result_plot.html")
        print(f"Saving plot to {output_file}...")
        fig.write_html(output_file, auto_open=True)
    
    def calculate_stresses(self, displacements, elements, AKT, NT, E, nu):
        """
        Обчислює усереднені тензори напружень у вузлах.
        Повертає список списків [sigma_xx, sigma_yy, sigma_zz, sigma_xy, sigma_yz, sigma_xz] для кожного вузла.
        """
        # 1. Підготовка матриці пружності D (Закон Гука для 3D) [cite: 33, 53]
        # D пов'язує деформації з напруженнями: sigma = D * epsilon
        G = E / (2 * (1 + nu))  # Модуль зсуву
        lam = (E * nu) / ((1 + nu) * (1 - 2 * nu)) # Параметр Ляме

        # Матриця D розміром 6x6
        D = np.array([
            [lam + 2*G, lam,       lam,       0, 0, 0],
            [lam,       lam + 2*G, lam,       0, 0, 0],
            [lam,       lam,       lam + 2*G, 0, 0, 0],
            [0,         0,         0,         G, 0, 0],
            [0,         0,         0,         0, G, 0],
            [0,         0,         0,         0, 0, G]
        ])

        # Ініціалізація масивів для накопичення напружень
        num_nodes = len(AKT)
        node_stresses = np.zeros((num_nodes, 6)) # Сума напружень у вузлі
        node_counts = np.zeros(num_nodes)        # Кількість елементів, що містять цей вузол

        # 2. Локальні координати вузлів стандартного елемента (20 шт) [cite: 341]
        # Це ті самі точки, що й у local_points, але нам треба знати їх (alpha, beta, gamma)
        # для підстановки у функції форми.
        local_coords = local_points # Вони у вас вже задані глобально як local_points

        # 3. Цикл по всіх елементах
        for el_idx, element_nodes_indices in enumerate(NT):
            # Отримуємо глобальні координати вузлів цього елемента
            el_global_coords = [AKT[i] for i in element_nodes_indices]
            
            # Отримуємо переміщення вузлів цього елемента (U_e)
            # displacements - це плоский список [u1_x, u1_y, u1_z, u2_x, ...], тому треба витягувати по 3 значення
            U_e = []
            for node_idx in element_nodes_indices:
                base_idx = 3 * node_idx
                U_e.append(displacements[base_idx])     # ux
                U_e.append(displacements[base_idx + 1]) # uy
                U_e.append(displacements[base_idx + 2]) # uz
            U_e = np.array(U_e) # Вектор переміщень елемента (розмір 60)

            # 4. Цикл по вузлах елемента для розрахунку напружень у них [cite: 633]
            for local_node_idx in range(20):
                alpha, beta, gamma = local_coords[local_node_idx]
                global_node_idx = element_nodes_indices[local_node_idx]

                # 4a. Обчислення похідних функцій форми (dPhi/dalpha, ...) у цьому вузлі
                # Використовуємо ваші існуючі функції
                if local_node_idx > 7: # Серединні вузли
                    dPhi_dLocal = self.DFIABD_center_side(alpha, beta, gamma, alpha, beta, gamma) # Тут alpha_i = alpha
                    # УВАГА: Ваші функції DFIABD приймають (alpha, beta, gamma, alpha_i, beta_i, gamma_i)
                    # Але нам треба повний набір похідних для всіх 20 функцій форми в точці (alpha, beta, gamma).
                    # Тому нам треба викликати це в циклі для всіх 20 функцій j=0..19
                else:
                    pass 

                # Оскільки ваша реалізація DFIABD специфічна (повертає значення лише для однієї i-ї функції),
                # нам треба зібрати матрицю Якобіана J і похідні dPhi/dX, dPhi/dY, dPhi/dZ.
                
                # --- Початок обчислення B-матриці (Деформаційної матриці) ---
                B = np.zeros((6, 60)) # Матриця зв'язку деформацій і переміщень: epsilon = B * U_e
                
                # Спочатку знайдемо Якобіан у цьому вузлі
                # J = [dx/dalpha, dy/dalpha... ]
                J = np.zeros((3, 3))
                dPhi_dLocal_all = [] # Зберігаємо похідні всіх 20 функцій по alpha, beta, gamma

                for j in range(20):
                    a_j, b_j, g_j = local_coords[j]
                    if j > 7:
                        derivs = self.DFIABD_center_side(alpha, beta, gamma, a_j, b_j, g_j)
                    else:
                        derivs = self.DFIABD_angle(alpha, beta, gamma, a_j, b_j, g_j)
                    
                    dPhi_dLocal_all.append(derivs) # [dPhi_j/dalpha, dPhi_j/dbeta, dPhi_j/dgamma]

                    # Формування Якобіана: Sum(x_j * dPhi_j/dLocal)
                    J[0, 0] += el_global_coords[j][0] * derivs[0] # dx/dalpha
                    J[0, 1] += el_global_coords[j][1] * derivs[0] # dy/dalpha
                    J[0, 2] += el_global_coords[j][2] * derivs[0] # dz/dalpha
                    
                    J[1, 0] += el_global_coords[j][0] * derivs[1] # dx/dbeta
                    J[1, 1] += el_global_coords[j][1] * derivs[1] # dy/dbeta
                    J[1, 2] += el_global_coords[j][2] * derivs[1] # dz/dbeta

                    J[2, 0] += el_global_coords[j][0] * derivs[2] # dx/dgamma
                    J[2, 1] += el_global_coords[j][1] * derivs[2] # dy/dgamma
                    J[2, 2] += el_global_coords[j][2] * derivs[2] # dz/dgamma

                try:
                    invJ = np.linalg.inv(J) # Обернений Якобіан
                except np.linalg.LinAlgError:
                    continue # Пропускаємо вироджені елементи (якщо є)

                # Тепер формуємо B-матрицю
                # Нам треба похідні по глобальних координатах dPhi/dX = invJ * dPhi/dLocal
                for j in range(20):
                    # Вектор похідних [dPhi/dalpha, dPhi/dbeta, dPhi/dgamma]
                    local_derivs = np.array(dPhi_dLocal_all[j])
                    global_derivs = np.dot(invJ, local_derivs) # [dPhi/dx, dPhi/dy, dPhi/dz]
                    
                    dN_dx = global_derivs[0]
                    dN_dy = global_derivs[1]
                    dN_dz = global_derivs[2]

                    # Заповнюємо B-матрицю (див. теорію МСЕ, напр. Zienkiewicz)
                    # Структура стовпчиків для j-го вузла (u, v, w)
                    idx = 3 * j
                    # epsilon_x
                    B[0, idx] = dN_dx
                    # epsilon_y
                    B[1, idx + 1] = dN_dy
                    # epsilon_z
                    B[2, idx + 2] = dN_dz
                    # gamma_xy
                    B[3, idx] = dN_dy
                    B[3, idx + 1] = dN_dx
                    # gamma_yz
                    B[4, idx + 1] = dN_dz
                    B[4, idx + 2] = dN_dy
                    # gamma_xz
                    B[5, idx] = dN_dz
                    B[5, idx + 2] = dN_dx

                # 4b. Обчислення деформацій epsilon = B * U_e
                epsilon = np.dot(B, U_e)

                # 4c. Обчислення напружень sigma = D * epsilon [cite: 60]
                sigma = np.dot(D, epsilon)

                # 5. Накопичення результатів для усереднення [cite: 635]
                node_stresses[global_node_idx] += sigma
                node_counts[global_node_idx] += 1

        # 6. Усереднення
        # Уникаємо ділення на нуль (для вузлів, які не увійшли в жоден елемент, хоча таких не має бути)
        node_counts[node_counts == 0] = 1 
        averaged_stresses = node_stresses / node_counts[:, None]

        return averaged_stresses.tolist()


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Main App", size=wx.Size(200, 800))
        panel = MyPanel(self)


if __name__ == "__main__":
    local_points = [
        [-1, 1, -1],  # 1
        [1, 1, -1],  # 2
        [1, -1, -1],  # 3
        [-1, -1, -1],  # 4
        [-1, 1, 1],  # 5
        [1, 1, 1],  # 6
        [1, -1, 1],  # 7
        [-1, -1, 1],  # 8
        [0, 1, -1],  # 9
        [1, 0, -1],  # 10
        [0, -1, -1],  # 11
        [-1, 0, -1],  # 12
        [-1, 1, 0],  # 13
        [1, 1, 0],  # 14
        [1, -1, 0],  # 15
        [-1, -1, 0],  # 16
        [0, 1, 1],  # 17
        [1, 0, 1],  # 18
        [0, -1, 1],  # 19
        [-1, 0, 1]  # 20
    ]
    # en\tau
    local_2d_points = [
        [-1, -1],  # 1
        [1, -1],  # 2
        [1, 1],  # 3
        [-1, 1],  # 4
        [0, -1],  # 5
        [1, 0],  # 6
        [0, 1],  # 7
        [-1, 0]  # 8
    ]

    elements = []
    AKT = []
    NT = []
    # навантаження закріплених
    ZU = []
    # навантажений елемент
    ZP = []
    DFIABG = []
    DFIXYZ = []
    DJ = []
    FE = []
    F = []
    MG = []
    nol_shist = math.sqrt(0.6)
    alpha_for = [-nol_shist, 0, nol_shist]
    beta_for = [-nol_shist, 0, nol_shist]
    gamma_for = [-nol_shist, 0, nol_shist]
    eta_for = [-nol_shist, 0, nol_shist]
    tau_for = [-nol_shist, 0, nol_shist]

    c_1 = 5 / 9
    c_2 = 8 / 9
    c_3 = 5 / 9

    E = 0
    nu = 0
    P = 0

    liambda = 0
    mu = 0

    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()