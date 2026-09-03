from __future__ import annotations

from typing import Iterable, Tuple
from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "same_period_setup_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class SamePeriodSetupSwap:
    """Intercambia un setup activo por uno inactivo dentro del mismo período.

    Movimiento: (t, i_out, i_in) con sol[i_out][t] = True y sol[i_in][t] = False.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Tuple[int, int, int]]:
        inst = self.problem.inst
        for t in range(inst.n_periods):
            on = [i for i in range(inst.n_items) if sol[i][t]]
            off = [i for i in range(inst.n_items) if not sol[i][t]]
            for i_out in on:
                for i_in in off:
                    yield (t, i_out, i_in)

    def apply(self, sol, m):
        t, i_out, i_in = m
        s = [list(r) for r in sol]
        s[i_out][t] = False
        s[i_in][t] = True
        return tuple(tuple(r) for r in s)

    def undo(self, sol, m):
        t, i_out, i_in = m
        s = [list(r) for r in sol]
        s[i_out][t] = True
        s[i_in][t] = False
        return tuple(tuple(r) for r in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SamePeriodSetupSwap(problem)
