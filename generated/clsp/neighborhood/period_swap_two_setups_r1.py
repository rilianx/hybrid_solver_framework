from __future__ import annotations

from typing import Iterable
import random

from examples.lotsizing.problem_model import Solution, CLSPInstance, LotSizingModel


COMPONENT = {
    "name": "period_swap_two_setups",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "same_period_only": {"type": "bool", "range": [0, 1]},
        "max_candidates": {"type": "int", "range": [1, 10]},
    },
}


class PeriodSwapTwoSetups:
    """Intercambia la presencia de setup entre dos ítems en un período.
    Movimiento = (t, i, j).
    """

    def __init__(self, problem: LotSizingModel, same_period_only: bool = True, max_candidates: int = 5):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.same_period_only = same_period_only
        self.max_candidates = max_candidates

    def moves(self, sol: Solution) -> Iterable[tuple[int, int, int]]:
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        emitted = 0
        for t in range(n_periods):
            on = [i for i in range(n_items) if sol[i][t]]
            off = [i for i in range(n_items) if not sol[i][t]]
            if len(on) < 1 or len(off) < 1:
                continue
            for i in on:
                for j in off:
                    yield (t, i, j)
                    emitted += 1
                    if emitted >= self.max_candidates:
                        return

    def apply(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        t, i, j = m
        return tuple(
            tuple(
                (False if i2 == i and tt == t else True if i2 == j and tt == t else sol[i2][tt])
                for tt in range(self.inst.n_periods)
            )
            for i2 in range(self.inst.n_items)
        )

    def undo(self, sol: Solution, m: tuple[int, int, int]) -> Solution:
        t, i, j = m
        return tuple(
            tuple(
                (True if i2 == i and tt == t else False if i2 == j and tt == t else sol[i2][tt])
                for tt in range(self.inst.n_periods)
            )
            for i2 in range(self.inst.n_items)
        )

    def delta(self, sol: Solution, m: tuple[int, int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, same_period_only: bool = True, max_candidates: int = 5):
    return PeriodSwapTwoSetups(problem, same_period_only=same_period_only, max_candidates=max_candidates)
