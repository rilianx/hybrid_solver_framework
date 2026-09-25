from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import Solution


COMPONENT = {
    "name": "bridge_setup_removal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class BridgeSetupRemoval:
    """Vecindario elemental de desplazamiento de un setup a un período adyacente.

    Mantiene la idea de reubicar patrones de setups, pero explora ambas
    direcciones (adelantar o retrasar un setup en un solo período). Esto permite
    generar mejoras que no se obtienen con un simple merge hacia atrás.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                if t > 0 and not sol[i][t - 1]:
                    yield (i, t, -1)
                if t + 1 < n_periods and not sol[i][t + 1]:
                    yield (i, t, 1)

    def apply(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        i, t, direction = m
        nt = t + direction
        rows = [list(row) for row in sol]
        rows[i][t] = False
        rows[i][nt] = True
        return tuple(tuple(row) for row in rows)

    def undo(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        i, t, direction = m
        nt = t + direction
        rows = [list(row) for row in sol]
        rows[i][nt] = False
        rows[i][t] = True
        return tuple(tuple(row) for row in rows)

    def delta(self, sol: Solution, m: tuple[int, int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BridgeSetupRemoval(problem)
