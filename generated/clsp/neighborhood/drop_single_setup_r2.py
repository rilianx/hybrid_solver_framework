from __future__ import annotations

from typing import Iterable, Tuple, Dict, Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "drop_single_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


Move = Tuple[int, int, int]


class DropSingleSetupNeighborhood:
    """Vecindario de reubicación de un setup: desplaza un único setup a un período vecino.

    El movimiento cambia exactamente dos bits del patrón:
    - apaga el setup original (i, t_from)
    - enciende un setup vecino (i, t_to)

    Esto mantiene la idea de "liberar" un período poco útil, pero genera vecinos
    distintos de un simple `setup_flip`.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Move]:
        n_periods = len(sol[0]) if sol else 0
        for i, row in enumerate(sol):
            for t, v in enumerate(row):
                if not v:
                    continue

                # Mover a un período anterior si está libre
                if t > 0 and not row[t - 1]:
                    yield (i, t, t - 1)

                # Mover a un período posterior si está libre
                if t + 1 < n_periods and not row[t + 1]:
                    yield (i, t, t + 1)

    def apply(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = True
        s[i][t_to] = False
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DropSingleSetupNeighborhood(problem)
