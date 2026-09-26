from __future__ import annotations

from random import Random
from typing import Iterable

from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "two_opt_reversal_neighborhood",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "sample_size": {"type": "int", "range": [1, 100]},
    },
}


class TwoOptReversalNeighborhood:
    """Reversa un segmento contiguo del gran tour. Movimiento = (i, j) con i < j."""

    def __init__(self, problem, sample_size: int = 20):
        self.problem = problem
        self.sample_size = int(sample_size)

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        tour = canonical(sol)
        n = len(tour)
        for i in range(n - 1):
            for j in range(i + 1, n):
                yield (i, j)

    def sample(self, sol, k: int, rng: Random) -> list[tuple[int, int]]:
        tour = canonical(sol)
        n = len(tour)
        all_moves = [(i, j) for i in range(n - 1) for j in range(i + 1, n)]
        if not all_moves or k <= 0:
            return []
        k = min(k, len(all_moves))
        return rng.sample(all_moves, k)

    def apply(self, sol, m) -> tuple[int, ...]:
        tour = list(canonical(sol))
        i, j = m
        if i >= j:
            return canonical(tuple(tour))
        tour[i : j + 1] = reversed(tour[i : j + 1])
        return canonical(tuple(tour))

    def undo(self, sol, m) -> tuple[int, ...]:
        return self.apply(sol, m)

    def delta(self, sol, m) -> float:
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))


def build_component(problem, **params):
    sample_size = params.get("sample_size", 20)
    return TwoOptReversalNeighborhood(problem, sample_size=sample_size)
