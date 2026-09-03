from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "left_shift_setup_chain",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class LeftShiftSetupChainNeighborhood:
    """Vecindario de redistribución: desplaza un setup una posición a la izquierda cuando eso preserva la estructura."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        for i, row in enumerate(sol):
            for t in range(1, len(row)):
                if row[t] and not row[t - 1]:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t] = False
        s[i][t - 1] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t - 1] = False
        s[i][t] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return LeftShiftSetupChainNeighborhood(problem)
