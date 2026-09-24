from __future__ import annotations

from typing import Iterable

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "double_retiming_block_move",
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


class DoubleRetimingBlockMoveNeighborhood:
    """Vecindario elemental de retiming: alterna un único setup y lo deja autocontenido.

    El movimiento es auto-inverso:
    - m = (i, t)
    - se conmuta el valor de y[i, t]

    Esto mantiene exactamente:
    undo(apply(sol, m)) == sol
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(n_periods):
                yield (i, t)

    def apply(self, sol, m):
        i, t = m
        s = [list(row) for row in sol]
        s[i][t] = not s[i][t]
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DoubleRetimingBlockMoveNeighborhood(problem)
