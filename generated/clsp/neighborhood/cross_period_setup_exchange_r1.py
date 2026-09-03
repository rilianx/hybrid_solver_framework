from __future__ import annotations

from typing import Iterable, Tuple
from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "cross_period_setup_exchange",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CrossPeriodSetupExchange:
    """Intercambia un setup activo en un período por un setup inactivo en otro período.

    Movimiento: (i_out, t_out, i_in, t_in) con sol[i_out][t_out] = True y
    sol[i_in][t_in] = False.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Tuple[int, int, int, int]]:
        inst = self.problem.inst
        active = [(i, t) for i in range(inst.n_items) for t in range(inst.n_periods) if sol[i][t]]
        inactive = [(i, t) for i in range(inst.n_items) for t in range(inst.n_periods) if not sol[i][t]]
        for i_out, t_out in active:
            for i_in, t_in in inactive:
                if (i_out, t_out) != (i_in, t_in):
                    yield (i_out, t_out, i_in, t_in)

    def apply(self, sol, m):
        i_out, t_out, i_in, t_in = m
        s = [list(r) for r in sol]
        s[i_out][t_out] = False
        s[i_in][t_in] = True
        return tuple(tuple(r) for r in s)

    def undo(self, sol, m):
        i_out, t_out, i_in, t_in = m
        s = [list(r) for r in sol]
        s[i_out][t_out] = True
        s[i_in][t_in] = False
        return tuple(tuple(r) for r in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CrossPeriodSetupExchange(problem)
