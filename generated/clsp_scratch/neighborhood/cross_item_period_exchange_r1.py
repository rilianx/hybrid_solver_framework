from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import Solution


COMPONENT = {
    "name": "cross_item_period_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CrossItemPeriodExchange:
    """Intercambia patrones de dos setups entre dos ítems y dos períodos.
    Movimiento = (i1, t1, i2, t2, a11, a12, a21, a22), donde aab son los valores
    originales de las cuatro celdas. La operación alterna:
      - (i1,t1) y (i2,t2) se apagan
      - (i1,t2) y (i2,t1) se encienden
    Si alguna celda destino ya estaba activa, el efecto neto puede ser una reducción
    de setups conservando la inversa exacta.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, int, int, bool, bool, bool, bool]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i1 in range(n_items):
            for i2 in range(i1 + 1, n_items):
                for t1 in range(n_periods):
                    if not sol[i1][t1]:
                        continue
                    for t2 in range(n_periods):
                        if t1 == t2 or not sol[i2][t2]:
                            continue
                        yield (
                            i1, t1, i2, t2,
                            bool(sol[i1][t1]),
                            bool(sol[i1][t2]),
                            bool(sol[i2][t1]),
                            bool(sol[i2][t2]),
                        )

    def apply(self, sol: Solution, m: tuple[int, int, int, int, bool, bool, bool, bool]) -> Solution:
        i1, t1, i2, t2, a11, a12, a21, a22 = m
        rows = [list(row) for row in sol]
        rows[i1][t1] = False
        rows[i2][t2] = False
        rows[i1][t2] = True
        rows[i2][t1] = True
        return tuple(tuple(row) for row in rows)

    def undo(self, sol: Solution, m: tuple[int, int, int, int, bool, bool, bool, bool]) -> Solution:
        i1, t1, i2, t2, a11, a12, a21, a22 = m
        rows = [list(row) for row in sol]
        rows[i1][t1] = a11
        rows[i1][t2] = a12
        rows[i2][t1] = a21
        rows[i2][t2] = a22
        return tuple(tuple(row) for row in rows)

    def delta(self, sol: Solution, m: tuple[int, int, int, int, bool, bool, bool, bool]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CrossItemPeriodExchange(problem)
