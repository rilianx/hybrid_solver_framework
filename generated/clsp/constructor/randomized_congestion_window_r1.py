from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, Solution

COMPONENT = {
    "name": "randomized_congestion_window",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "alpha": {"type": "float", "range": [0.05, 1.0]},
        "window": {"type": "int", "range": [1, 12]},
    },
}


class RandomizedCongestionWindow:
    """Selecciona una ventana de períodos congestionados y asigna setups con una RCL aleatoria.
    Enfatiza diversidad estructural: la decisión se guía por saturación de capacidad.
    """

    def __init__(self, alpha: float = 0.3, window: int = 4) -> None:
        self.alpha = alpha
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]

        per_period_demand = [sum(inst.demand[i][t] for i in range(n)) for t in range(T)]
        slack_score = [inst.capacity[t] - per_period_demand[t] - sum(inst.setup_time) for t in range(T)]

        # Ítems en orden aleatorio reproducible, pero guiado por su "densidad".
        items = list(range(n))
        items.sort(key=lambda i: (sum(inst.demand[i]), -inst.setup_cost[i], inst.setup_time[i]), reverse=True)
        # Pequeña perturbación determinista por rng.
        for k in range(len(items) - 1, 0, -1):
            j = rng.randint(0, k)
            items[k], items[j] = items[j], items[k]

        for i in items:
            total_d = sum(inst.demand[i][t] for t in range(T))
            if total_d <= 1e-9:
                continue

            # Ventana de períodos candidatos: prioriza los menos congestionados.
            candidates = list(range(T))
            candidates.sort(key=lambda t: (slack_score[t], inst.capacity[t], -t), reverse=True)
            candidates = candidates[: max(1, min(T, self.window))]

            # Lista restringida aleatoria.
            best = max(1, int(len(candidates) * self.alpha))
            choice_pool = candidates[:best]
            t = rng.choice(choice_pool)
            y[i][t] = True

        sol = tuple(tuple(row) for row in y)
        if not problem_is_feasible_fallback(inst, sol):
            sol = deterministic_fill_missing(inst, sol, rng)
        return sol


def problem_is_feasible_fallback(inst: CLSPInstance, sol: Solution) -> bool:
    for i in range(inst.n_items):
        if sum(inst.demand[i][t] for t in range(inst.n_periods)) > 1e-9 and not any(sol[i][t] for t in range(inst.n_periods)):
            return False
    return True


def deterministic_fill_missing(inst: CLSPInstance, sol: Solution, rng: Random) -> Solution:
    n, T = inst.n_items, inst.n_periods
    y = [list(row) for row in sol]
    for i in range(n):
        if any(y[i]):
            continue
        # Elige el período con más capacidad y menor índice.
        t = max(range(T), key=lambda tt: (inst.capacity[tt], -tt))
        y[i][t] = True
    return tuple(tuple(row) for row in y)


def build_component(problem: Any, alpha: float = 0.3, window: int = 4):
    return RandomizedCongestionWindow(alpha=float(alpha), window=int(window))
