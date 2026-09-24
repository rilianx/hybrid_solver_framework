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

    Movimiento m = (i, t): si hay setup en i,t y también en i,t-1, apaga el setup
    de t. El LP de la vista del problema redistribuye la producción y decide si la
    fusión es factible/costosa; aquí solo se propone la estructura de movimiento.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol: Solution) -> Iterable[tuple[int, int]]:
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for i in range(n_items):
            row = sol[i]
            for t in range(1, n_periods):
                if row[t] and row[t - 1]:
                    yield (i, t)

    def apply(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        row = list(sol[i])
        row[t] = False
        new_sol = [list(r) for r in sol]
        new_sol[i] = row
        return tuple(tuple(r) for r in new_sol)

    def undo(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        row = list(sol[i])
        row[t] = True
        new_sol = [list(r) for r in sol]
        new_sol[i] = row
        return tuple(tuple(r) for r in new_sol)

    def delta(self, sol: Solution, m: tuple[int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return LeftShiftMerge(problem)
