from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "drop_single_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class DropSingleSetupNeighborhood:
    """Vecindario de poda: apaga un único setup (i, t) y deja que el LP reacomode producción e inventario."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        for i, row in enumerate(sol):
            for t, v in enumerate(row):
                if v:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DropSingleSetupNeighborhood(problem)
