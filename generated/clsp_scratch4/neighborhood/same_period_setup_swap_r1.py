from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import CLSPInstance, var_name

COMPONENT = {
    "name": "same_period_setup_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.to_assignment", "ProblemModel.from_assignment", "problem.inst"],
    "params": {},
}


class SamePeriodSetupSwapNeighborhood:
    """Intercambia un setup activo por otro inactivo en el mismo período.

    Movimiento: (i_on, i_off, t), con sol[i_on][t] = True y sol[i_off][t] = False.
    Es un operador de reasignación entre ítems que explora qué producto merece
    ocupar la capacidad de un período dado.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for t in range(n_periods):
            on = [i for i in range(n_items) if sol[i][t]]
            off = [i for i in range(n_items) if not sol[i][t]]
            for i_on in on:
                for i_off in off:
                    yield (i_on, i_off, t)

    def apply(self, sol, m):
        i_on, i_off, t = m
        s = [list(row) for row in sol]
        s[i_on][t] = False
        s[i_off][t] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i_on, i_off, t = m
        s = [list(row) for row in sol]
        s[i_on][t] = True
        s[i_off][t] = False
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SamePeriodSetupSwapNeighborhood(problem)
