from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "randomized_priority_capacity_packing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "alpha": {"type": "float", "range": [0.05, 1.0]},
        "period_bias": {"type": "float", "range": [0.0, 2.0]},
    },
}


class RandomizedPriorityCapacityPackingConstructor:
    """GRASP-like: selecciona setups por prioridad aleatorizada y empaca capacidad por período."""

    def __init__(self, problem, alpha: float = 0.3, period_bias: float = 1.0):
        self.problem = problem
        self.alpha = alpha
        self.period_bias = period_bias

    def _empty(self, inst: CLSPInstance):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int, val: bool):
        row = list(sol[i])
        row[t] = val
        sol2 = list(sol)
        sol2[i] = tuple(row)
        return tuple(sol2)

    def _priority(self, inst: CLSPInstance, i: int, t: int) -> float:
        future = sum(inst.demand[i][tt] for tt in range(t, inst.n_periods))
        urgent = inst.demand[i][t] + 0.5 * future
        denom = 1.0 + inst.setup_time[i] + inst.setup_cost[i] / 100.0
        return (urgent * (1.0 + self.period_bias / (1.0 + t))) / denom

    def _repair(self, sol, rng: Random):
        inst = self.problem.inst
        for _ in range(6 * inst.n_items * inst.n_periods + 1):
            if self.problem.is_feasible(sol):
                return sol
            detail = getattr(self.problem.mip, "shortage_detail", lambda s: {}) (sol)
            if not detail:
                break
            items = sorted(detail.items(), key=lambda kv: (-kv[1], kv[0][1], kv[0][0]))
            i, t = items[0][0]
            sol = self._set(sol, i, t, True)
            for tt in range(t - 1, -1, -1):
                if self.problem.is_feasible(sol):
                    return sol
                if rng.random() < 0.2:
                    sol = self._set(sol, i, tt, True)
        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        sol = self._empty(inst)
        n_items, n_periods = inst.n_items, inst.n_periods

        for t in range(n_periods):
            cap_left = inst.capacity[t]
            cand = [(self._priority(inst, i, t), i) for i in range(n_items) if inst.demand[i][t] > 0 or sum(inst.demand[i][tt] for tt in range(t, n_periods)) > 0]
            if not cand:
                continue
            cand.sort(reverse=True)
            rcl_size = max(1, int(len(cand) * self.alpha))
            rcl = cand[:rcl_size]
            rng.shuffle(rcl)
            for _, i in rcl:
                if sol[i][t]:
                    continue
                if inst.setup_time[i] <= cap_left + 1e-9:
                    sol = self._set(sol, i, t, True)
                    cap_left -= inst.setup_time[i]

        for i in range(n_items):
            if not any(sol[i][t] for t in range(n_periods)):
                t = max(range(n_periods), key=lambda tt: inst.demand[i][tt])
                sol = self._set(sol, i, t, True)

        sol = self._repair(sol, rng)
        if not self.problem.is_feasible(sol):
            for i in range(n_items):
                for t in range(n_periods):
                    if inst.demand[i][t] > 0:
                        sol = self._set(sol, i, t, True)
                        if self.problem.is_feasible(sol):
                            return sol
        return sol


def build_component(problem, alpha: float = 0.3, period_bias: float = 1.0):
    return RandomizedPriorityCapacityPackingConstructor(problem, alpha=alpha, period_bias=period_bias)
