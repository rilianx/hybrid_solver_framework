from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "dense_full_setup_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class DenseFullSetupConstructor:
    """Constructor con varias semillas densas/factibles y selección por objetivo."""

    def __init__(self, problem=None):
        self.problem = problem

    def _is_feasible(self, sol) -> bool:
        prob = self.problem
        if prob is not None and hasattr(prob, "is_feasible"):
            try:
                return bool(prob.is_feasible(sol))
            except Exception:
                pass
        return True

    def _objective(self, sol):
        prob = self.problem
        if prob is not None and hasattr(prob, "objective"):
            try:
                return prob.objective(sol)
            except Exception:
                return None
        return None

    def _all_setups(self, inst: CLSPInstance):
        return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _demand_dense(self, inst: CLSPInstance):
        sol = []
        for i in range(inst.n_items):
            row = [False] * inst.n_periods
            for t in range(inst.n_periods):
                if inst.demand[i][t] > 0:
                    row[t] = True
            sol.append(tuple(row))
        return tuple(sol)

    def _first_demand_setups(self, inst: CLSPInstance):
        sol = []
        for i in range(inst.n_items):
            row = [False] * inst.n_periods
            first = None
            for t in range(inst.n_periods):
                if inst.demand[i][t] > 0:
                    first = t
                    break
            if first is not None:
                row[first] = True
            sol.append(tuple(row))
        return tuple(sol)

    def _last_demand_setups(self, inst: CLSPInstance):
        sol = []
        for i in range(inst.n_items):
            row = [False] * inst.n_periods
            last = None
            for t in range(inst.n_periods - 1, -1, -1):
                if inst.demand[i][t] > 0:
                    last = t
                    break
            if last is not None:
                row[last] = True
            sol.append(tuple(row))
        return tuple(sol)

    def _backward_greedy(self, inst: CLSPInstance):
        n_items = inst.n_items
        n_periods = inst.n_periods
        demand = inst.demand
        capacity = inst.capacity
        setup_time = inst.setup_time

        remaining = [sum(demand[i][t] for t in range(n_periods)) for i in range(n_items)]
        sol_rows = [[False] * n_periods for _ in range(n_items)]

        for t in range(n_periods - 1, -1, -1):
            residual = capacity[t]
            items = [i for i in range(n_items) if remaining[i] > 0]
            items.sort(key=lambda i: (-remaining[i], setup_time[i], i))

            for i in items:
                if remaining[i] <= 0:
                    continue
                st = setup_time[i]
                if st > residual:
                    continue
                qty = residual - st
                if qty <= 0:
                    continue
                qty = min(qty, remaining[i])
                if qty <= 0:
                    continue
                sol_rows[i][t] = True
                remaining[i] -= qty
                residual -= qty + st

        return tuple(tuple(row) for row in sol_rows)

    def build(self, inst: CLSPInstance, rng: Random):
        candidates = [
            self._first_demand_setups(inst),
            self._last_demand_setups(inst),
            self._demand_dense(inst),
            self._backward_greedy(inst),
            self._all_setups(inst),
        ]

        best_sol = None
        best_obj = None

        for sol in candidates:
            if not self._is_feasible(sol):
                continue
            obj = self._objective(sol)
            if obj is None:
                if best_sol is None:
                    best_sol = sol
                continue
            if best_obj is None or obj < best_obj:
                best_obj = obj
                best_sol = sol

        if best_sol is not None:
            return best_sol

        dense = self._demand_dense(inst)
        if self._is_feasible(dense):
            return dense
        return self._all_setups(inst)


def build_component(problem, **params):
    _ = getattr(problem, "inst", None)
    return DenseFullSetupConstructor(problem=problem)
