from __future__ import annotations

from typing import Iterable, Protocol, Any


COMPONENT = {
    "name": "merge_with_previous_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_lookback": {"type": "int", "range": [1, 6]},
        "min_savings_margin": {"type": "float", "range": [0.0, 1000.0]},
    },
}


class MergeWithPreviousSetupNeighborhood:
    """Neighborhood that proposes removing a setup when an earlier setup exists."""

    def __init__(self, problem: Any, max_lookback: int = 3, min_savings_margin: float = 0.0):
        self.problem = problem
        self.inst = problem.inst
        self.max_lookback = max_lookback
        self.min_savings_margin = min_savings_margin

    def _can_merge(self, sol, i: int, t: int) -> bool:
        if not sol[i][t]:
            return False
        prev = [tt for tt in range(max(0, t - self.max_lookback), t) if sol[i][tt]]
        if not prev:
            return False
        return True

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        inst = self.inst
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                if not self._can_merge(sol, i, t):
                    continue
                demand_here = inst.demand[i][t]
                if demand_here <= self.min_savings_margin:
                    continue
                yield (i, t)

    def apply(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t] = not s[i][t]
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_lookback: int = 3, min_savings_margin: float = 0.0):
    return MergeWithPreviousSetupNeighborhood(
        problem,
        max_lookback=max_lookback,
        min_savings_margin=min_savings_margin,
    )
