from dataclasses import dataclass, field
from typing import List

@dataclass
class SimulationParams:
    """
    Контейнер (DTO) для зберігання вхідних параметрів симуляції.
    Містить значення за замовчуванням, якщо користувач нічого не ввів.
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

    liambda: float = E / ((1 + nu) * (1 - 2 * nu))
    mu: float = E / (2 * (1 + nu))
    
    # Список індексів елементів, які закріплюються (вісь, сторона)
    stick_element: tuple = (2, 'min')
    
    # Сторона, де застосовується тиск (вісь, сторона)
    pressure_side: tuple = (2, 'max')