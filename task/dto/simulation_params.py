from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SimulationParams:
    """
    Контейнер для зберігання вхідних параметрів симуляції.
    """
    # Геометричні розміри
    a: float = 2.0
    b: float = 2.0
    c: float = 10.0
    
    # Кількість розбиттів (сітка)
    na: int = 2
    nb: int = 2
    nc: int = 3
    
    # Фізичні властивості та навантаження
    E: float = 1
    nu: float = 0.3
    P: float = 5000.0

    # Параметри Ламе
    liambda: float = 0.0    # Показує зв'язок між стисканням в одному напрямку і розширенням в іншому
    mu: float = 0.0         # Показує опір матеріалу зміні форми без зміни об'єму

    # ZU — список індексів вузлів AKT, де закріплення (формула 30)
    zu_node_indices: Optional[List[int]] = None

    # ZP — список пар (індекс елемента, номер грані 1-6) для навантаження (формула 31)
    # Номери граней: 1=X_min, 2=X_max, 3=Y_min, 4=Y_max, 5=Z_min, 6=Z_max
    zp_entries: Optional[List[tuple]] = None
