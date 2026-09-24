from __future__ import annotations

from typing import Iterable

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "double_retiming_block_move",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": [
        "ProblemModel.objective",
        "ProblemModel.to_assignment",
        "ProblemModel.from_assignment",
        "problem.inst",
    ],
    "params": {},
}


class DoubleRetimingBlockMoveNeighborhood:
    """Vecindario por intercambio de dos setups del mismo ítem.

    El movimiento es elemental y auto-inverso:
    - m = (i, t1, t2) con t1 != t2
    - se intercambia el estado de y[i, t1] y y[i, t2]

    Esto preserva exactamente la propiedad undo(apply(sol, m)) == sol.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def moves(self, sol) -> Iterable[tuple[int, int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            active = [t for t in range(n_periods) if sol[i][t]]
            for a in range(len(active)):
                for b in range(a + 1, len(active)):
                    yield (i, active[a], active[b])

    def apply(self, sol, m):
        i, t1, t2 = m
        if t1 == t2:
            return sol
        s = [list(row) for row in sol]
        s[i][t1], s[i][t2] = s[i][t2], s[i][t1]
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DoubleRetimingBlockMoveNeighborhood(problem)
