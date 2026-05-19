from dataclasses import dataclass
from typing import List, Any

@dataclass
class SimulationResults:
    """
    Датаклас для зберігання всіх результатів МСЕ-розрахунку.

    Позначення: N = nqp (кількість вузлів), M = nel (кількість елементів).
    """
    # M × 27 × 3×3  — матриці Якобі (27 точок Гауса, 3×3 кожна) для кожного з M елементів
    DJ: List[Any] = None
    # M × 27        — детермінанти Якобі |J| у кожній точці Гауса кожного елемента
    DJ_det: List[Any] = None
    # M × 27 × 20 × 3 — похідні функцій форми у глобальних координатах (∂φ/∂x, ∂φ/∂y, ∂φ/∂z)
    DFIXYZ: List[Any] = None
    # M × 60 × 60   — локальні матриці жорсткості елементів (формула 43)
    MGE: List[Any] = None

    # N × 3  — глобальні координати всіх вузлів (x, y, z)
    AKT: List[Any] = None
    # M × 20 — матриця зв'язності: глобальні номери 20 вузлів кожного елемента
    NT: List[Any] = None

    # M × 60 — вектори вузлових сил елементів (результат інтегрування тиску)
    FE: List[Any] = None
    # 3N     — вектор переміщень усіх вузлів (Ux₁,Uy₁,Uz₁, Ux₂,...), розв'язок MG·U=F
    displacements: Any = None
    # N × 6  — напруження у вузлах: [σx, σy, σz, τxy, τyz, τzx] (формула 48)
    stresses: List[Any] = None
    # N × 3  — головні напруження у вузлах: σ₁ ≥ σ₂ ≥ σ₃ (формула 49)
    principal_stresses: List[Any] = None

    def is_calculated(self) -> bool:
        return self.DJ is not None