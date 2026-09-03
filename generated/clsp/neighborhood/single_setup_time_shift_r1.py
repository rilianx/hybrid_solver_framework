from __future__ import annotations

from typing import Iterable
import random

from examples.lotsizing.problem_model import Solution, CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "single_setup_time_shift",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "radius": {"type": "int", "range": [1, 3]},
        "bidirectional": {"type": "bool", "range": [0, 1]},
    },
}


class SingleSetupTimeShift:
    """Mueve un setup de un ítem un número pequeño de períodos hacia adelante o atrás.
    Movimiento = (i, t_from, t_to).
    """

    def __init__(self, problem: LotSizingModel, radius: int = 1, bidirectional: bool = True):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.radius = radius
        self.bidirectional = bidirectional

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, int]]:
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        for i in range(n_items):
            for t_from in range(n_periods):
                if not sol[i][t_from]:
                    continue
                lo = max(0, t_from - self.radius)
                hi = min(n_periods - 1, t_from + self.radius)
                for t_to in range(lo, hi + 1):
                    if t_to == t_from:
                        continue
                    if self.bidirectional or t_to < t_from:
                        yield (i, t_from, t_to)

    def apply(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        i, t_from, t_to = m
        return tuple(
            tuple(
                (t_to == t and i2 == i) or (t == t_from and i2 == i and False) or sol[i2][t]
                if False
                else (t == t_to if i2 == i and t == t_to else sol[i2][t])
                for t in range(self.inst.n_periods)
            )
            for i2 in range(self.inst.n_items)
        )

    def undo(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        i, t_from, t_to = m
        return tuple(
            tuple(
                (t == t_from if i2 == i and t == t_from else sol[i2][t]) if not (i2 == i and t == t_to) else False
                for t in range(self.inst.n_periods)
            )
            for i2 in range(self.inst.n_items)
        )

    def delta(self, sol: Solution, m: tuple[int, int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, radius: int = 1, bidirectional: bool = True):
    return SingleSetupTimeShift(problem, radius=radius, bidirectional=bidirectional)
