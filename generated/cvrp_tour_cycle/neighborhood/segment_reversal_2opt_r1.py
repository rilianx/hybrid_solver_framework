from __future__ import annotations

from typing import Iterable
import random


COMPONENT = {
    "name": "segment_reversal_2opt",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "problem.parts.canonical"],
    "params": {},
}


class SegmentReversal2Opt:
    """Invierte un segmento contiguo del gran tour.
    Movimiento: (i, j) con i < j, invierte sol[i:j+1].
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        n = len(sol)
        for i in range(n - 1):
            for j in range(i + 1, n):
                yield (i, j)

    def apply(self, sol, m) -> tuple:
        i, j = m
        s = list(sol)
        s[i : j + 1] = reversed(s[i : j + 1])
        return self.problem.parts.canonical(tuple(s))

    def undo(self, sol, m) -> tuple:
        # La inversión es su propia inversa.
        return self.apply(sol, m)

    def delta(self, sol, m) -> float:
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))


def build_component(problem, **params):
    return SegmentReversal2Opt(problem)
