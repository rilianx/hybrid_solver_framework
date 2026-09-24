from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import CLSPInstance, var_name

COMPONENT = {
    "name": "backward_merge_shift",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": [
        "ProblemModel.objective",
        "ProblemModel.to_assignment",
        "ProblemModel.from_assignment",
        "problem.inst",
    ],
    "params": {},
}


class BackwardMergeShiftNeighborhood:
    """Mueve un setup de un período a un período anterior vacío del mismo ítem.

    Movimiento: (i, t_from, t_to) con t_to < t_from, sol[i][t_from] == True y
    sol[i][t_to] == False.

    La idea sigue siendo desplazar un setup hacia atrás para favorecer fusiones
    implícitas por inventario, pero el movimiento es elemental y reversible.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            active = [t for t in range(n_periods) if sol[i][t]]
            inactive = [t for t in range(n_periods) if not sol[i][t]]
            for t_from in active:
                for t_to in inactive:
                    if t_to < t_from:
                        yield (i, t_from, t_to)

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

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BackwardMergeShiftNeighborhood(problem)
