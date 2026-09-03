from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, Solution, LotSizingModel

COMPONENT = {
    "name": "backward_capacity_packing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class BackwardCapacityPacking:
    """Construye de atrás hacia delante, empaquetando demanda futura en capacidad libre.
    Idea: producir lo más tarde posible para reducir inventario, respetando capacidad por período.
    """

    def __init__(self) -> None:
        pass

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        remaining = [float(sum(inst.demand[i][t] for t in range(T))) for i in range(n)]
        y = [[False for _ in range(T)] for _ in range(n)]

        # Procesar períodos desde el último al primero.
        for t in range(T - 1, -1, -1):
            cap_left = float(inst.capacity[t])

            # Candidatos con demanda remanente; prioriza ítems "baratos" en setup time.
            candidates = [i for i in range(n) if remaining[i] > 1e-9]
            candidates.sort(key=lambda i: (inst.setup_time[i], -remaining[i], inst.setup_cost[i]))

            for i in candidates:
                if remaining[i] <= 1e-9:
                    continue
                # Si abrimos un setup, necesitamos reservar su tiempo.
                if cap_left <= inst.setup_time[i] + 1e-9:
                    continue
                y[i][t] = True
                cap_left -= inst.setup_time[i]

                # Produce tanto como quepa, dejando holgura mínima.
                qty = min(remaining[i], cap_left)
                remaining[i] -= qty
                cap_left -= qty

                if cap_left <= 1e-9:
                    break

        sol = tuple(tuple(row) for row in y)
        if not problem_is_feasible_fallback(inst, sol):
            sol = repair_by_earliest_shift(inst, sol, rng)
        return sol


def problem_is_feasible_fallback(inst: CLSPInstance, sol: Solution) -> bool:
    # Fallback estructural sin depender del ProblemModel; la validación final la hace problem.is_feasible.
    # Aquí solo comprobamos que haya algún setup por cada ítem con demanda total positiva.
    for i in range(inst.n_items):
        if sum(inst.demand[i][t] for t in range(inst.n_periods)) > 1e-9 and not any(sol[i][t] for t in range(inst.n_periods)):
            return False
    return True


def repair_by_earliest_shift(inst: CLSPInstance, sol: Solution, rng: Random) -> Solution:
    # Reparación conservadora: si algún ítem no tiene setup, lo coloca donde haya más capacidad "probable".
    n, T = inst.n_items, inst.n_periods
    y = [list(row) for row in sol]
    for i in range(n):
        if any(y[i]):
            continue
        best_t = min(range(T), key=lambda t: (inst.capacity[t], t))
        y[i][best_t] = True
    return tuple(tuple(row) for row in y)


def build_component(problem: Any, **params):
    return BackwardCapacityPacking()
