from dataclasses import dataclass
from typing import List, Any

@dataclass
class SimulationResults:
    """
    Датаклас для зберігання всіх результатів МСЕ.
    """
    DJ: List[Any] = None   # Масиви матриць Якобі
    DJ_det: List[Any] = None       # Детермінанти
    DFIXYZ: List[Any] = None      # Реальні похідні функцій форми
    MGE: List[Any] = None         # Локальні матриці жорсткості елементів

    AKT: List[Any] = None         # Глобальні координати вузлів (AKT)
    NT: List[Any] = None  
    
    FE: List[Any] = None          # Локальні вектори сил (FE)  
    displacements: Any = None     # Глобальний вектор переміщень (U)
    stresses: List[Any] = None    # Напруження у вузлах

    def is_calculated(self) -> bool:
        """Перевіряє, чи розрахунок вже було виконано."""
        return self.jacobians is not None