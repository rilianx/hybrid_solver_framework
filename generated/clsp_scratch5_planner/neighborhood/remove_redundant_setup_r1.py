from __future__ import annotations

import random
from typing import Iterable, Protocol, runtime_checkable

from examples.lotsizing.problem_model import ProblemModel, Solution, Move


COMPONENT = {
    "name": "remove_redundant_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class RemoveRedundantSetupNeighborhood:
    """Eliminación selectiva de un setup: apaga un setup existente y deja
    que el LP de cantidades/inventarios reajuste el coste global.

    Movimiento = (i, t), indicando el ítem i y período t cuyo setup se apaga.
    """

    def __init__(self, problem: ProblemModel):
        self.problem = problem

    def moves(self, sol: Solution) -> Iterable[Move]:
        # Todos los setups activos son candidatos; el evaluador determinará
        # cuáles son realmente redundantes.
        for i, row in enumerate(sol):
            for t, active in enumerate(row):
                if active:
                    yield (i, t)

    def apply(self, sol: Solution, m: Move) -> Solution:
        i, t = m
        return tuple(
            tuple((False if (ii == i and tt == t) else cell) for tt, cell in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def undo(self, sol: Solution, m: Move) -> Solution:
        i, t = m
        return tuple(
            tuple((True if (ii == i and tt == t) else cell) for tt, cell in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def delta(self, sol: Solution, m: Move) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return RemoveRedundantSetupNeighborhood(problem)
