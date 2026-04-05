from dataclasses import dataclass
from typing import List, Any

@dataclass
class SimulationResults:
    """
    Датаклас для зберігання всіх результатів МСЕ.
    """
    DJ: List[Any] = None
    DJ_det: List[Any] = None
    DFIXYZ: List[Any] = None
    MGE: List[Any] = None

    AKT: List[Any] = None
    NT: List[Any] = None

    FE: List[Any] = None
    displacements: Any = None
    stresses: List[Any] = None
    principal_stresses: List[Any] = None

    def is_calculated(self) -> bool:
        return self.DJ is not None