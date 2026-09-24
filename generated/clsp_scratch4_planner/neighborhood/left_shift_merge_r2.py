from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import Solution


COMPONENT = {
    "name": "left_shift_merge",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class LeftShiftMerge:
    """Vecindario de fusión hacia la izquierda.

    Movimiento m = (i, t): para un setup activo en i,t con t>0, intenta
    consolidarlo en t-1 activando el setup anterior si hace falta y apagando
    el de t. Esto desplaza producción hacia atrás sin reordenar entre ítems.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol: Solution) -> Iterable[tuple[int, int]]:
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for i in range(n_items):
            row = sol[i]
            for t in range(1, n_periods):
                if row[t]:
                    yield (i, t)

    def apply(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        new_sol = [list(r) for r in sol]
        new_sol[i][t] = False
        new_sol[i][t - 1] = True
        return tuple(tuple(r) for r in new_sol)

    def undo(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        new_sol = [list(r) for r in sol]
        new_sol[i][t] = True
        new_sol[i][t - 1] = False
        return tuple(tuple(r) for r in new_sol)

    def delta(self, sol: Solution, m: tuple[int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return LeftShiftMerge(problem)
