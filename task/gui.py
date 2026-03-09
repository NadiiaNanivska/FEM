import os
import numpy as np
import wx
from wx.lib.masked import NumCtrl

from task import constants
from task.windows.grid_result_viewer import GridResultsViewer
from task.windows.mge_viewer import MGEViewer
from task.dto.simulation_params import SimulationParams
from task.fem_functions.mesh_generator import MeshGenerator
from task.fem_functions.shape_functions import ShapeFunctionsMath
from task.windows.mesh_vizualizer import MeshVisualizer
from task.fem_functions.boundary_condition_manager import BoundaryConditionManager
from task.dto.simulation_results import SimulationResults

class MyPanel(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetBackgroundColour(wx.Colour(245, 245, 250))
        
        self.SetScrollRate(5, 5)

        label_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.a_entry = wx.TextCtrl(self, value="4.0")
        self.b_entry = wx.TextCtrl(self, value="5.0")
        self.c_entry = wx.TextCtrl(self, value="3.0")

        self.n_A = wx.TextCtrl(self, value="2")
        self.n_B = wx.TextCtrl(self, value="1")
        self.n_C = wx.TextCtrl(self, value="2")

        self.stick = wx.TextCtrl(self, value="2,min")

        self.E_entry = wx.TextCtrl(self, value="1")
        self.nu_entry = wx.TextCtrl(self, value="0.3")
        
        for ctrl in [self.a_entry, self.b_entry, self.c_entry, self.n_A, self.n_B, 
                     self.n_C, self.stick, self.E_entry, self.nu_entry]:
            ctrl.SetBackgroundColour(wx.Colour(255, 255, 255))
            ctrl.SetMinSize((150, 28))

        self.all_points_button = wx.Button(self, label="Розрахувати")
        self.all_points_button.Bind(wx.EVT_BUTTON, self.on_all_points_button)
        self.all_points_button.SetBackgroundColour(wx.Colour(52, 152, 219))
        self.all_points_button.SetMinSize((320, 40))
        calc_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.all_points_button.SetFont(calc_font)

        self.results = SimulationResults()

        self.btn_view_dj = wx.Button(self, label="Переглянути DJ та DFIXYZ")
        self.btn_view_mge = wx.Button(self, label="Переглянути MGE")
        self.btn_view_mesh = wx.Button(self, label="Переглянути 3D сітку")
        
        for btn in [self.btn_view_dj, self.btn_view_mge, self.btn_view_mesh]:
            btn.SetBackgroundColour(wx.Colour(46, 204, 113))
            btn.SetMinSize((320, 35))
            btn.SetFont(calc_font)
        
        self.btn_view_dj.Disable()
        self.btn_view_mge.Disable()
        self.btn_view_mesh.Disable()

        self.btn_view_dj.Bind(wx.EVT_BUTTON, self.on_view_dj)
        self.btn_view_mge.Bind(wx.EVT_BUTTON, self.on_view_mge)
        self.btn_view_mesh.Bind(wx.EVT_BUTTON, self.on_view_mesh)

        # Ліва колонка - параметри МСЕ
        left_box = wx.StaticBoxSizer(wx.VERTICAL, self, "Параметри МСЕ")
        left_box.SetMinSize((250, -1))
        
        left_box_ctrl = left_box.GetStaticBox()
        left_box_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        left_box_ctrl.SetFont(left_box_font)
        left_box_ctrl.SetForegroundColour(wx.Colour(52, 152, 219))
        
        n_x_label = wx.StaticText(self, label="n_x:")
        n_x_label.SetFont(label_font)
        left_box.Add(n_x_label, 0, wx.ALL, 5)
        left_box.Add(self.n_A, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        n_y_label = wx.StaticText(self, label="n_y:")
        n_y_label.SetFont(label_font)
        left_box.Add(n_y_label, 0, wx.ALL, 5)
        left_box.Add(self.n_B, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        n_z_label = wx.StaticText(self, label="n_z:")
        n_z_label.SetFont(label_font)
        left_box.Add(n_z_label, 0, wx.ALL, 5)
        left_box.Add(self.n_C, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        a_x_label = wx.StaticText(self, label="A_x:")
        a_x_label.SetFont(label_font)
        left_box.Add(a_x_label, 0, wx.ALL, 5)
        left_box.Add(self.a_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        a_y_label = wx.StaticText(self, label="A_y:")
        a_y_label.SetFont(label_font)
        left_box.Add(a_y_label, 0, wx.ALL, 5)
        left_box.Add(self.b_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        a_z_label = wx.StaticText(self, label="A_z:")
        a_z_label.SetFont(label_font)
        left_box.Add(a_z_label, 0, wx.ALL, 5)
        left_box.Add(self.c_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        stick_label = wx.StaticText(self, label="Закріплена грань (0: X, 1: Y, 2: Z):")
        stick_label.SetFont(label_font)
        left_box.Add(stick_label, 0, wx.ALL, 5)
        left_box.Add(self.stick, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        # Права колонка - фізичні властивості
        right_box = wx.StaticBoxSizer(wx.VERTICAL, self, "Фізичні властивості")
        right_box.SetMinSize((200, -1))
        
        right_box_ctrl = right_box.GetStaticBox()
        right_box_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        right_box_ctrl.SetFont(right_box_font)
        right_box_ctrl.SetForegroundColour(wx.Colour(231, 76, 60))
        
        e_label = wx.StaticText(self, label="E (модуль Юнга):")
        e_label.SetFont(label_font)
        right_box.Add(e_label, 0, wx.ALL, 5)
        right_box.Add(self.E_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        
        nu_label = wx.StaticText(self, label="ν (коефіцієнт Пуассона):")
        nu_label.SetFont(label_font)
        right_box.Add(nu_label, 0, wx.ALL, 5)
        right_box.Add(self.nu_entry, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        params_sizer = wx.BoxSizer(wx.HORIZONTAL)
        params_sizer.Add(left_box, 1, wx.ALL | wx.EXPAND, 10)
        params_sizer.Add(right_box, 1, wx.ALL | wx.EXPAND, 10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(params_sizer, 0, wx.ALL | wx.EXPAND, 0)
        
        # Кнопки з кращим стилем
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.all_points_button, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_mesh, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_dj, 0, wx.ALL | wx.EXPAND, 8)
        button_sizer.Add(self.btn_view_mge, 0, wx.ALL | wx.EXPAND, 8)
        
        sizer.Add(button_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(sizer)
        
        sizer.Layout()
        self.FitInside()

    def _validate_stick_element(self, value: str) -> tuple:
        """
        Валідує та розбирає формат закріпленої грані: вісь,напрям
        Повертає кортеж (вісь, напрям)
        Викидає ValueError з описом помилки
        """
        value = value.strip()
        if not value:
            raise ValueError("Закріплена грань не може бути порожною! Формат: вісь,напрям (наприклад: 0,min)")
        
        parts = [p.strip() for p in value.split(',')]
        if len(parts) != 2:
            raise ValueError("Формат закріпленої грані: вісь,напрям (наприклад: 0,min або 2,max)")
        
        axis_str, direction = parts
        
        try:
            axis = int(axis_str)
        except ValueError:
            raise ValueError("Вісь має бути числом: 0 (X), 1 (Y) або 2 (Z)")
        
        if axis not in [0, 1, 2]:
            raise ValueError("Вісь може бути тільки: 0 (X), 1 (Y), 2 (Z)")
        
        direction = direction.lower()
        if direction not in ['min', 'max']:
            raise ValueError("Напрям має бути: 'min' або 'max'")
        
        return (axis, direction)

    def get_params_from_ui(self) -> SimulationParams:
        """
        Зчитує дані з графічного інтерфейсу та пакує їх в об'єкт DTO.
        """
        def parse_float(ctrl, default):
            return float(ctrl.GetValue()) if ctrl.GetValue().strip() else default
            
        def parse_int(ctrl, default):
            return int(ctrl.GetValue()) if ctrl.GetValue().strip() else default

        params = SimulationParams()

        params.a = parse_float(self.a_entry, params.a)
        params.b = parse_float(self.b_entry, params.b)
        params.c = parse_float(self.c_entry, params.c)
        
        params.na = parse_int(self.n_A, params.na)
        params.nb = parse_int(self.n_B, params.nb)
        params.nc = parse_int(self.n_C, params.nc)

        params.E = parse_float(self.E_entry, params.E)
        params.nu = parse_float(self.nu_entry, params.nu)

        params.stick_element = self._validate_stick_element(self.stick.GetValue())

        return params

    def on_all_points_button(self, event):
        """
        Головний контролер: оркеструє процес розрахунку та візуалізації.
        """
        try:
            params = self.get_params_from_ui()
        except ValueError as e:
            wx.MessageBox(str(e), "Помилка введення даних", wx.OK | wx.ICON_ERROR)
            return

        # 2. ГЕОМЕТРІЯ
        mesh_gen = MeshGenerator()
        elements = mesh_gen.create_points(params.a, params.b, params.c, params.na, params.nb, params.nc)
        AKT = mesh_gen.separate_point(params.a, params.b, params.c, params.na, params.nb, params.nc)
        NT = mesh_gen.NT_transform(AKT, elements)

        # 3. КРАЙОВІ УМОВИ
        bc_manager = BoundaryConditionManager()
        ZU = bc_manager.ZU_Chose(AKT, axis=params.stick_element[0], side=params.stick_element[1])
        print(f"Закріплені вузли (ZU): {ZU}")
        # 4. МАТЕМАТИКА
        math_engine = ShapeFunctionsMath()
        DFIABG = math_engine.DFIABG_Create()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        dfiabg_path = os.path.join(script_dir, "statics", "DFIABG_matrix.txt")
        math_engine.save_dfiabg_to_txt(DFIABG, dfiabg_path)

        DJ = []
        DJ_det = []
        DFIXYZ = []

        for i, element_coords in enumerate(elements):
            jacobians = math_engine.create_jacobian_for_element(element_coords, DFIABG)
            DJ.append(jacobians)
            
            det_j_for_element = [math_engine.calculate_determinant(J) for J in jacobians]
            DJ_det.append(det_j_for_element)
            
            dfixyz_element = math_engine.calculate_dfixyz_for_element(jacobians, DFIABG)
            DFIXYZ.append(dfixyz_element)
            
            if i == 0:
                if hasattr(math_engine, 'save_dfixyz_to_txt'):
                    dfixyz_path = os.path.join(script_dir, "statics", "DFIXYZ_element_0.txt")
                    math_engine.save_dfixyz_to_txt(dfixyz_element, dfixyz_path, element_id=0)

        list_of_MGE = []
        for i in range(len(elements)):
            list_of_MGE.append(
                math_engine.calc_MGE(DFIXYZ[i], DJ_det[i], [constants.c_1, constants.c_2, constants.c_3], 
                                     params.liambda, params.nu, params.mu))
        
        self.results.DJ = DJ
        self.results.DJ_det = DJ_det
        self.results.DFIXYZ = DFIXYZ
        self.results.AKT = AKT
        self.results.NT = NT
        self.results.MGE = list_of_MGE

        self.btn_view_dj.Enable()
        self.btn_view_mesh.Enable()
        self.btn_view_mge.Enable() 
        
        wx.MessageBox("Розрахунок успішно завершено!", "Успіх", wx.OK | wx.ICON_INFORMATION)

    def on_view_dj(self, event):
        viewer = GridResultsViewer(self, self.results)
        viewer.Show()

    def on_view_mge(self, event):
        viewer = MGEViewer(self, self.results.MGE)
        viewer.Show()

    def on_view_mesh(self, event):
        visualizer = MeshVisualizer()
        fig = visualizer.plot_initial_mesh(self.results.AKT, self.results.NT)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "statics", "result_plot.html")
        fig.write_html(output_file, auto_open=True)


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Симуляція МСЕ", size=wx.Size(750, 700))
        self.SetBackgroundColour(wx.Colour(245, 245, 250))
        
        self.Centre()
        
        panel = MyPanel(self)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()