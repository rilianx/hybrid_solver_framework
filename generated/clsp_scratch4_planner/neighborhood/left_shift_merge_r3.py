from __future__ import annotations

from typing import Iterable, Tuple
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

    Movimiento m = (i, t, left_active):
    - si hay setup en (i, t) con t > 0, intenta eliminarlo;
    - si (i, t-1) estaba apagado, lo enciende para mantener la factibilidad
      estructural del patrón de setups;
    - si (i, t-1) ya estaba activo, simplemente apaga (i, t).

    Esta parametrización hace el movimiento perfectamente reversible.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol: Solution) -> Iterable[Tuple[int, int, bool]]:
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for i in range(n_items):
            row = sol[i]
            for t in range(1, n_periods):
                if row[t]:
                    yield (i, t, bool(row[t - 1]))

    def apply(self, sol: Solution, m: Tuple[int, int, bool]) -> Solution:
        i, t, left_active = m
        new_sol = [list(r) for r in sol]
        new_sol[i][t] = False
        if not left_active:
            new_sol[i][t - 1] = True
        return tuple(tuple(r) for r in new_sol)

    def undo(self, sol: Solution, m: Tuple[int, int, bool]) -> Solution:
        i, t, left_active = m
        new_sol = [list(r) for r in sol]
        new_sol[i][t] = True
        if not left_active:
            new_sol[i][t - 1] = False
        return tuple(tuple(r) for r in new_sol)

    def delta(self, sol: Solution, m: Tuple[int, int, bool]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return LeftShiftMerge(problem)
