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
    """Vecindario de desplazamiento elemental de un setup un período hacia la izquierda.

    Mantiene la idea de modificar únicamente el patrón binario de setups, pero
    ahora propone movimientos que pueden adelantar producción a un período
    anterior cuando hay holgura, lo que genera mejoras que no son alcanzables
    por un simple backward-merge de un setup puente.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol: Solution) -> Iterable[tuple[int, int]]:
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        for i in range(n_items):
            for t in range(1, n_periods):
                if sol[i][t] and not sol[i][t - 1]:
                    yield (i, t)

    def apply(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        rows = [list(row) for row in sol]
        rows[i][t] = False
        rows[i][t - 1] = True
        return tuple(tuple(row) for row in rows)

    def undo(self, sol: Solution, m: tuple[int, int]) -> Solution:
        i, t = m
        rows = [list(row) for row in sol]
        rows[i][t] = True
        rows[i][t - 1] = False
        return tuple(tuple(row) for row in rows)

    def delta(self, sol: Solution, m: tuple[int, int]) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BridgeSetupRemoval(problem)
