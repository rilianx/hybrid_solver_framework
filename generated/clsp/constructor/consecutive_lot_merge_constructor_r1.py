from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "consecutive_lot_merge_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "merge_bias": {"type": "float", "range": [0.0, 1.0]},
        "sparsify": {"type": "bool", "range": [0, 1]},
    },
}


class ConsecutiveLotMergeConstructor:
    """Empieza con lot-for-lot por ítem y fusiona setups consecutivos cuando compensa inventario vs. setup."""

    def __init__(self, problem, merge_bias: float = 0.5, sparsify: bool = True):
        self.problem = problem
        self.merge_bias = merge_bias
        self.sparsify = sparsify

    def _empty(self, inst: CLSPInstance):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int, val: bool):
        row = list(sol[i])
        row[t] = val
        sol2 = list(sol)
        sol2[i] = tuple(row)
        return tuple(sol2)

    def _first_feasible(self, inst: CLSPInstance):
        sol = self._empty(inst)
        for i in range(inst.n_items):
            for t, d in enumerate(inst.demand[i]):
                if d > 0:
                    sol = self._set(sol, i, t, True)
        return sol

    def _merge(self, sol, rng: Random):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        for i in range(n_items):
            ones = [t for t in range(n_periods) if sol[i][t]]
            for a, b in zip(ones, ones[1:]):
                if b == a + 1:
                    if rng.random() <= self.merge_bias:
                        sol = self._set(sol, i, a, False)
        return sol

    def _repair(self, sol, rng: Random):
        inst = self.problem.inst
        if self.problem.is_feasible(sol):
            return sol
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                if inst.demand[i][t] > 0 and not sol[i][t]:
                    sol = self._set(sol, i, t, True)
                    if self.problem.is_feasible(sol):
                        return sol
        detail = getattr(self.problem.mip, "shortage_detail", lambda s: {}) (sol)
        for (i, t), _q in sorted(detail.items(), key=lambda kv: -kv[1]):
            for tt in range(t, -1, -1):
                if not sol[i][tt]:
                    sol = self._set(sol, i, tt, True)
                    if self.problem.is_feasible(sol):
                        return sol
        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        sol = self._first_feasible(inst)
        sol = self._merge(sol, rng)

        if self.sparsify:
            # elimina setups redundantes aislados si siguen cubiertas las demandas
            for i in range(inst.n_items):
                for t in range(inst.n_periods):
                    if sol[i][t] and rng.random() < 0.5:
                        trial = self._set(sol, i, t, False)
                        if self.problem.is_feasible(trial):
                            sol = trial

        sol = self._repair(sol, rng)
        if not self.problem.is_feasible(sol):
            for i in range(inst.n_items):
                best_t = max(range(inst.n_periods), key=lambda tt: inst.demand[i][tt])
                sol = self._set(sol, i, best_t, True)
        return sol


def build_component(problem, merge_bias: float = 0.5, sparsify: bool = True):
    return ConsecutiveLotMergeConstructor(problem, merge_bias=merge_bias, sparsify=sparsify)
