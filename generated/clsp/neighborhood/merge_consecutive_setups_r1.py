from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "merge_consecutive_setups",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class MergeConsecutiveSetupsNeighborhood:
    """Vecindario de compactación temporal: elimina un bloque contiguo de setups de un mismo ítem."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        n_periods = self.problem.inst.n_periods
        for i, row in enumerate(sol):
            t = 0
            while t < n_periods:
                if row[t]:
                    a = t
                    while t + 1 < n_periods and row[t + 1]:
                        t += 1
                    b = t
                    for start in range(a, b + 1):
                        for end in range(start, b + 1):
                            yield (i, start, end)
                t += 1

    def apply(self, sol, m):
        i, a, b = m
        s = [list(row) for row in sol]
        for t in range(a, b + 1):
            s[i][t] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, a, b = m
        s = [list(row) for row in sol]
        for t in range(a, b + 1):
            s[i][t] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return MergeConsecutiveSetupsNeighborhood(problem)
