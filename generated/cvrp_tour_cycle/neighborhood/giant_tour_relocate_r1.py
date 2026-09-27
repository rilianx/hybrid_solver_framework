from __future__ import annotations

from random import Random
from typing import Iterable

COMPONENT = {
    "name": "giant_tour_relocate",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {
        "max_samples": {"type": "int", "range": [1, 50]},
    },
}


class GiantTourRelocateNeighborhood:
    """Reubica un cliente a otra posición del gran tour: movimiento = (i, j)."""

    def __init__(self, problem, max_samples: int = 15):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.max_samples = int(max_samples)

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        tour = self.canonical(sol)
        n = len(tour)
        for i in range(n):
            for j in range(n):
                if i != j:
                    yield (i, j)

    def sample(self, sol, k: int, rng: Random) -> list[tuple[int, int]]:
        tour = self.canonical(sol)
        n = len(tour)
        all_moves = [(i, j) for i in range(n) for j in range(n) if i != j]
        if k >= len(all_moves):
            rng.shuffle(all_moves)
            return all_moves
        return rng.sample(all_moves, k)

    def apply(self, sol, m: tuple[int, int]):
        tour = list(self.canonical(sol))
        i, j = m
        if i == j:
            return self.canonical(tuple(tour))
        c = tour.pop(i)
        if j > i:
            j -= 1
        tour.insert(j, c)
        return self.canonical(tuple(tour))

    def delta(self, sol, m: tuple[int, int]) -> float:
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))


def build_component(problem, max_samples: int = 15):
    return GiantTourRelocateNeighborhood(problem, max_samples=max_samples)
