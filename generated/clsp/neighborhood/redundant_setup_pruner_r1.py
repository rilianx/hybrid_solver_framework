from __future__ import annotations

from typing import Iterable, Tuple
from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "redundant_setup_pruner",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class RedundantSetupPruner:
    """Elimina setups intermedios redundantes de una cadena del mismo ítem.

    Movimiento: (i, t) significa apagar sol[i][t] si el período t está flanqueado
    por setups del mismo ítem en algún período anterior y posterior.
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[Tuple[int, int]]:
        inst = self.problem.inst
        for i in range(inst.n_items):
            row = sol[i]
            prev_on = False
            next_on = [False] * inst.n_periods
            seen = False
            for t in range(inst.n_periods - 1, -1, -1):
                next_on[t] = seen
                seen = seen or row[t]
            for t in range(inst.n_periods):
                if row[t] and prev_on and next_on[t]:
                    yield (i, t)
                prev_on = prev_on or row[t]

    def apply(self, sol, m):
        i, t = m
        s = [list(r) for r in sol]
        s[i][t] = False
        return tuple(tuple(r) for r in s)

    def undo(self, sol, m):
        i, t = m
        s = [list(r) for r in sol]
        s[i][t] = True
        return tuple(tuple(r) for r in s)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return RedundantSetupPruner(problem)
