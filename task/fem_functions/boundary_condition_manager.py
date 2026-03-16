class BoundaryConditionManager:
    """
    Клас відповідає за роботу з крайовими умовами моделі.
    Визначає вузли для жорсткого закріплення (ZU) та поверхні для навантаження (ZP).
    """
    
    def __init__(self):
        pass

    def ZU_Chose(self, eleme, axis=2, side='min'):
        """
        Знаходить вузли на заданій грані для їх закріплення.
        :param eleme: список усіх вузлів (AKT)
        :param axis: вісь, перпендикулярно до якої лежить грань (0: X, 1: Y, 2: Z)
        :param side: 'min' (початок координат) або 'max' (кінець координат)
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
        Знаходить 8 локальних вузлів (координат) на заданій грані одного кубика.
        Використовується для прикладання поверхневого тиску (FE_Calc).
        
        :param element_nodes: Список координат 20 вузлів одного елемента (з AKT).
        :param axis: вісь, перпендикулярно до якої лежить грань (0: X, 1: Y, 2: Z)
        :param side: 'min' або 'max'
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