from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "cumulative_backward_repair",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 8]},
        "random_tie_break": {"type": "bool", "range": [0, 1]},
    },
}


class CumulativeBackwardRepairConstructor:
    """Construye un plan lote-a-lote y, si queda infactible, adelanta setups a períodos anteriores con holgura."""

    def __init__(self, problem, lookahead: int = 3, random_tie_break: bool = True):
        self.problem = problem
        self.lookahead = lookahead
        self.random_tie_break = random_tie_break

    def _empty(self, inst: CLSPInstance):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int, val: bool):
        row = list(sol[i])
        row[t] = val
        sol2 = list(sol)
        sol2[i] = tuple(row)
        return tuple(sol2)

    def _repair(self, sol, rng: Random):
        inst = self.problem.inst
        n_items, n_periods = inst.n_items, inst.n_periods

        for _ in range(4 * n_items * n_periods + 1):
            if self.problem.is_feasible(sol):
                return sol

            detail = getattr(self.problem.mip, "shortage_detail", lambda s: {}) (sol)
            if not detail:
                break

            (i, t), _q = max(detail.items(), key=lambda kv: kv[1])
            if not any(sol[i][tt] for tt in range(t + 1)):
                sol = self._set(sol, i, t, True)
                continue

            best_tt = None
            best_slack = -1.0
            lo = max(0, t - self.lookahead)
            for tt in range(lo, t):
                used = sum(
                    inst.setup_time[j] + (inst.demand[j][tt] if sol[j][tt] else 0.0)
                    for j in range(n_items)
                )
                slack = inst.capacity[tt] - used
                if slack > best_slack + 1e-9:
                    best_slack = slack
                    best_tt = tt

            if best_tt is None or best_slack <= 1e-9:
                sol = self._set(sol, i, t, True)
                continue

            sol = self._set(sol, i, best_tt, True)
            if best_tt != t and rng.random() < 0.5:
                sol = self._set(sol, i, t, False)

        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = self._empty(inst)

        remaining = [0.0] * n_items
        for i in range(n_items):
            remaining[i] = sum(inst.demand[i])

        for t in range(n_periods):
            cap_left = inst.capacity[t]
            candidates = list(range(n_items))
            if self.random_tie_break:
                rng.shuffle(candidates)

            for i in sorted(candidates, key=lambda k: (inst.holding_cost[k], inst.setup_cost[k], k), reverse=True):
                demand_t = inst.demand[i][t]
                future = sum(inst.demand[i][tt] for tt in range(t, n_periods))
                if demand_t > 0 or (future > 0 and (not any(sol[i][tt] for tt in range(t + 1)))):
                    if not sol[i][t]:
                        need = inst.setup_time[i]
                        if need <= cap_left + 1e-9:
                            sol = self._set(sol, i, t, True)
                            cap_left -= need

        sol = self._repair(sol, rng)
        if not self.problem.is_feasible(sol):
            for i in range(n_items):
                for t in range(n_periods):
                    if not sol[i][t] and inst.demand[i][t] > 0:
                        sol = self._set(sol, i, t, True)
                        if self.problem.is_feasible(sol):
                            break
                if self.problem.is_feasible(sol):
                    break
        return sol


def build_component(problem, lookahead: int = 3, random_tie_break: bool = True):
    return CumulativeBackwardRepairConstructor(problem, lookahead=lookahead, random_tie_break=random_tie_break)
