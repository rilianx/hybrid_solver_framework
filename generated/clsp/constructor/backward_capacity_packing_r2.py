from __future__ import annotations

from random import Random
from typing import Any, Optional

from examples.lotsizing.problem_model import CLSPInstance, Solution, LotSizingModel

COMPONENT = {
    "name": "backward_capacity_packing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class BackwardCapacityPacking:
    """Construcción conservadora de atrás hacia delante.

    Idea:
    - Para cada ítem, asegurar setups suficientes para cubrir su demanda en el horizonte.
    - Priorizar setups en el tramo [primer_período_con_demanda, último_período_con_demanda].
    - Si el problema ligado está disponible, aceptar solo patrones factibles.
    """

    def __init__(self, problem: Optional[LotSizingModel] = None) -> None:
        self.problem = problem

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]

        # Estrategia base: activar setups desde el primer hasta el último período con demanda.
        # Esto corrige el fallo contractual del módulo original: ningún ítem queda sin setup
        # antes de sus períodos de demanda.
        for i in range(n):
            demand_periods = [t for t in range(T) if inst.demand[i][t] > 1e-9]
            if not demand_periods:
                continue
            first_t = min(demand_periods)
            last_t = max(demand_periods)

            for t in range(first_t, last_t + 1):
                y[i][t] = True

        sol: Solution = tuple(tuple(row) for row in y)

        # Si tenemos el modelo ligado y el patrón no es factible, hacemos un ajuste
        # conservador añadiendo setups en períodos previos hasta obtener factibilidad
        # (sin movimientos compuestos ni cambios in-place).
        if self.problem is not None and not self.problem.is_feasible(sol):
            sol = self._repair_with_earlier_setups(inst, sol, rng)

        return sol

    def _repair_with_earlier_setups(
        self, inst: CLSPInstance, sol: Solution, rng: Random
    ) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [list(row) for row in sol]

        # Añadir setups en períodos más tempranos para ítems con demanda,
        # intentando preservar la idea de "producción lo más tarde posible".
        candidates = []
        for i in range(n):
            demand_periods = [t for t in range(T) if inst.demand[i][t] > 1e-9]
            if not demand_periods:
                continue
            first_t = min(demand_periods)
            for t in range(first_t - 1, -1, -1):
                if not y[i][t]:
                    candidates.append((inst.setup_time[i], t, i))

        candidates.sort(key=lambda x: (x[0], x[1], x[2]))

        for _, t, i in candidates:
            if self.problem.is_feasible(tuple(tuple(row) for row in y)):
                break
            y[i][t] = True

        sol2: Solution = tuple(tuple(row) for row in y)
        if self.problem.is_feasible(sol2):
            return sol2

        # Último recurso: garantizar que todo ítem con demanda tenga al menos
        # un setup en su primer período de demanda.
        y = [list(row) for row in sol2]
        for i in range(n):
            if any(inst.demand[i][t] > 1e-9 for t in range(T)) and not any(y[i]):
                first_t = min(t for t in range(T) if inst.demand[i][t] > 1e-9)
                y[i][first_t] = True

        sol3: Solution = tuple(tuple(row) for row in y)
        return sol3


def build_component(problem: Any, **params):
    return BackwardCapacityPacking(problem=problem)
