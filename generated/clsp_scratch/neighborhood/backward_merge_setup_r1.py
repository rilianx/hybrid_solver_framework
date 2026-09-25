from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import Solution


COMPONENT = {
    "name": "backward_merge_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class BackwardMergeSetup:
    """Fusiona un setup en t con el de t-1 del mismo ítem, eliminando el setup de t.
    Movimiento = (i, t, prev_on), donde prev_on indica si y[i][t-1] estaba activo.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, bool]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(1, n_periods):
                if sol[i][t]:
                    yield (i, t, bool(sol[i][t - 1]))

    def apply(self, sol: Solution, m: tuple[int, int, bool]) -> Solution:
        i, t, prev_on = m
        rows = [list(row) for row in sol]
        rows[i][t] = False
        if not prev_on:
            rows[i][t - 1] = True
        return tuple(tuple(row) for row in rows)

    def undo(self, sol: Solution, m: tuple[int, int, bool]) -> Solution:
        i, t, prev_on = m
        rows = [list(row) for row in sol]
        rows[i][t] = True
        if not prev_on:
            rows[i][t - 1] = False
        return tuple(tuple(row) for row in rows)

    def delta(self, sol: Solution, m: tuple[int, int, bool]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BackwardMergeSetup(problem)
