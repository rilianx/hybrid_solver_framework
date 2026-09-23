from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, Solution

COMPONENT = {
    "name": "earliest_slack_repair",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {"window": {"type": "int", "range": [1, 10]}},
}


class EarliestSlackRepair:
    """Parte de un esquema lot-for-lot y adelanta setups desde períodos congestionados
    hacia el período anterior con más holgura acumulada.
    """

    def __init__(self, window: int = 3) -> None:
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        y = [[False for _ in range(T)] for _ in range(n)]

        # Inicio: setup en el último período con demanda de cada ítem.
        last_demand = []
        for i in range(n):
            ts = [t for t in range(T) if inst.demand[i][t] > 1e-9]
            last_demand.append(max(ts) if ts else None)
        for i, t in enumerate(last_demand):
            if t is not None:
                y[i][t] = True

        # Reparación: mover setups hacia atrás si eso libera períodos saturados.
        for _ in range(max(1, self.window * T)):
            load = [sum(inst.setup_time[i] for i in range(n) if y[i][t]) for t in range(T)]
            improved = False
            congested = sorted(range(T), key=lambda t: (load[t] - inst.capacity[t], t), reverse=True)
            for t in congested:
                if load[t] <= inst.capacity[t] + 1e-9:
                    continue
                # Ítem candidato: setup movable hacia atrás.
                candidates = [i for i in range(n) if y[i][t]]
                candidates.sort(key=lambda i: (inst.setup_cost[i], -inst.setup_time[i], i))
                for i in candidates:
                    prevs = [tp for tp in range(max(0, t - self.window), t) if not y[i][tp]]
                    prevs.sort(key=lambda tp: (inst.capacity[tp] - load[tp], tp), reverse=True)
                    if not prevs:
                        continue
                    tp = prevs[0]
                    if load[tp] + inst.setup_time[i] <= inst.capacity[tp] + 1e-9:
                        y[i][t] = False
                        y[i][tp] = True
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break

        sol = tuple(tuple(row) for row in y)
        if not problem_is_feasible_fallback(inst, sol):
            sol = force_one_setup_per_item(inst, sol, rng)
        return sol


def problem_is_feasible_fallback(inst: CLSPInstance, sol: Solution) -> bool:
    for i in range(inst.n_items):
        if sum(inst.demand[i][t] for t in range(inst.n_periods)) > 1e-9 and not any(sol[i][t] for t in range(inst.n_periods)):
            return False
    return True


def force_one_setup_per_item(inst: CLSPInstance, sol: Solution, rng: Random) -> Solution:
    n, T = inst.n_items, inst.n_periods
    y = [list(row) for row in sol]
    for i in range(n):
        if not any(y[i]) and sum(inst.demand[i][t] for t in range(T)) > 1e-9:
            t = min(range(T), key=lambda tt: (inst.capacity[tt], tt))
            y[i][t] = True
    return tuple(tuple(row) for row in y)


def build_component(problem: Any, **params):
    return EarliestSlackRepair(window=int(params.get("window", 3)))
