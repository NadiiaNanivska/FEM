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