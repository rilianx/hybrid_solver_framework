COMPONENT = {
    "name": "pairwise_setup_shift",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}

from typing import Iterable
from examples.lotsizing.problem_model import var_name  # noqa: F401


class PairwiseSetupShiftNeighborhood:
    """Intercambia el estado de setup entre dos períodos para el mismo ítem: (i, t_from, t_to)."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple]:
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for i in range(n_items):
            for t_from in range(n_periods):
                if not sol[i][t_from]:
                    continue
                for t_to in range(n_periods):
                    if t_to != t_from:
                        yield (i, t_from, t_to)

    def apply(self, sol, m):
        i, t_from, t_to = m
        return tuple(
            tuple(
                (
                    sol[ii][t_to]
                    if ii == i and tt == t_from
                    else sol[ii][t_from]
                    if ii == i and tt == t_to
                    else bit
                )
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        # La operación es una transposición, por lo que es su propia inversa.
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return PairwiseSetupShiftNeighborhood(problem)
