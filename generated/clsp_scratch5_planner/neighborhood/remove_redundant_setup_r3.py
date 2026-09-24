from __future__ import annotations

from typing import Any, Iterable, Tuple

from examples.lotsizing.problem_model import Solution


Move = Tuple[int, int]


COMPONENT = {
    "name": "remove_redundant_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class RemoveRedundantSetupNeighborhood:
    """Neighborhood that removes a single active setup.

    Move = (i, t), meaning the setup y[i][t] is switched off.
    The LP behind the problem re-optimizes quantities/inventories.
    """

    def __init__(self, problem: Any):
        self.problem = problem

    def moves(self, sol: Solution) -> Iterable[Move]:
        for i, row in enumerate(sol):
            for t, active in enumerate(row):
                if active:
                    yield (i, t)

    def apply(self, sol: Solution, m: Move) -> Solution:
        i, t = m
        return tuple(
            tuple(False if (ii == i and tt == t) else cell for tt, cell in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def undo(self, sol: Solution, m: Move) -> Solution:
        i, t = m
        return tuple(
            tuple(True if (ii == i and tt == t) else cell for tt, cell in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def delta(self, sol: Solution, m: Move) -> float:
        new_sol = self.apply(sol, m)
        return self.problem.objective(new_sol) - self.problem.objective(sol)


def build_component(problem, **params):
    return RemoveRedundantSetupNeighborhood(problem)
