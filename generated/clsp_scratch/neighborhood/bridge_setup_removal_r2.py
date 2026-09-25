from __future__ import annotations

from typing import Iterable
from examples.lotsizing.problem_model import Solution


COMPONENT = {
    "name": "bridge_setup_removal",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class BridgeSetupRemoval:
    """Elimina un setup 'puente' de un ítem cuando existe setup antes y después.
    Si no hay puentes estrictos en la solución, ofrece una eliminación simple
    de cualquier setup presente para garantizar vecindario no vacío.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol: Solution) -> Iterable[tuple[int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        bridge_moves = []
        for i in range(n_items):
            for t in range(1, n_periods - 1):
                if sol[i][t] and sol[i][t - 1] and sol[i][t + 1]:
                    bridge_moves.append((i, t))

        if bridge_moves:
            for m in bridge_moves:
                yield m
            return

        for i in range(n_items):
            for t in range(n_periods):
                if sol[i][t]:
                    yield (i, t)

    def apply(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        rows = [list(row) for row in sol]
        rows[i][t] = False
        return tuple(tuple(row) for row in rows)

    def undo(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        rows = [list(row) for row in sol]
        rows[i][t] = True
        return tuple(tuple(row) for row in rows)

    def delta(self, sol: Solution, m: tuple[int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BridgeSetupRemoval(problem)
