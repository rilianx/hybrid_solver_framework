COMPONENT = {
    "name": "single_setup_removal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}

from typing import Iterable
from examples.lotsizing.problem_model import var_name  # noqa: F401


class SingleSetupRemovalNeighborhood:
    """Elimina un único setup y deja que el LP reasigne producción e inventario."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple]:
        for i, row in enumerate(sol):
            for t, active in enumerate(row):
                if active:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple((not bit) if (ii == i and tt == t) else bit for tt, bit in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SingleSetupRemovalNeighborhood(problem)
