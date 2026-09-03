from __future__ import annotations

from typing import Iterable, Tuple

from examples.lotsizing.problem_model import Solution, CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "single_setup_time_shift",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "radius": {"type": "int", "range": [1, 3]},
        "bidirectional": {"type": "bool", "values": [False, True]},
    },
}


class SingleSetupTimeShift:
    """Mueve un setup de un ítem a un período cercano.

    Movimiento: (i, t_from, t_to).
    Para garantizar ``undo(apply(sol, m)) == sol``, solo se generan movimientos
    hacia períodos destino que actualmente no tienen setup.
    """

    def __init__(self, problem: LotSizingModel, radius: int = 1, bidirectional: bool = True):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.radius = radius
        self.bidirectional = bidirectional

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, int]]:
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        for i in range(n_items):
            row = sol[i]
            for t_from in range(n_periods):
                if not row[t_from]:
                    continue
                lo = max(0, t_from - self.radius)
                hi = min(n_periods - 1, t_from + self.radius)
                for t_to in range(lo, hi + 1):
                    if t_to == t_from:
                        continue
                    if not self.bidirectional and t_to > t_from:
                        continue
                    if row[t_to]:
                        continue
                    yield (i, t_from, t_to)

    def apply(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        i, t_from, t_to = m
        if t_from == t_to:
            return sol

        new_sol = [list(row) for row in sol]
        new_sol[i][t_from] = False
        new_sol[i][t_to] = True
        return tuple(tuple(row) for row in new_sol)

    def undo(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        i, t_from, t_to = m
        if t_from == t_to:
            return sol

        new_sol = [list(row) for row in sol]
        new_sol[i][t_to] = False
        new_sol[i][t_from] = True
        return tuple(tuple(row) for row in new_sol)

    def delta(self, sol: Solution, m: tuple[int, int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, radius: int = 1, bidirectional: bool = True):
    return SingleSetupTimeShift(problem, radius=radius, bidirectional=bidirectional)
