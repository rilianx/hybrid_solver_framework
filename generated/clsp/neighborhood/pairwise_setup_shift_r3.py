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
    """Vecindario de reubicación/consolidación de setups entre dos períodos del mismo ítem.

    Un movimiento (i, t_from, t_to, y_to_old) apaga el setup en t_from y enciende
    el setup en t_to. Si t_to ya estaba activo, el movimiento consolida y elimina
    un setup, lo que suele generar mejoras desde soluciones tipo lot-for-lot.
    """

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
                    if t_to == t_from:
                        continue
                    # Permitimos tanto reubicación como consolidación.
                    # La consolidación (t_to ya activo) es la que puede mejorar
                    # directamente desde la solución inicial.
                    yield (i, t_from, t_to, bool(sol[i][t_to]))

    def apply(self, sol, m):
        i, t_from, t_to, _y_to_old = m
        return tuple(
            tuple(
                (
                    False if (ii == i and tt == t_from) else
                    True if (ii == i and tt == t_to) else
                    bit
                )
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        i, t_from, t_to, y_to_old = m
        return tuple(
            tuple(
                (
                    True if (ii == i and tt == t_from) else
                    y_to_old if (ii == i and tt == t_to) else
                    bit
                )
                for tt, bit in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return PairwiseSetupShiftNeighborhood(problem)
