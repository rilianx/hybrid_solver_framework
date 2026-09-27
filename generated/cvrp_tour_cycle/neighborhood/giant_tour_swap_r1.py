from __future__ import annotations

from random import Random
from typing import Iterable

COMPONENT = {
    "name": "giant_tour_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {
        "max_samples": {"type": "int", "range": [1, 50]},
    },
}


class GiantTourSwapNeighborhood:
    """Intercambio de dos clientes en el gran tour: movimiento = (i, j)."""

    def __init__(self, problem, max_samples: int = 15):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.max_samples = int(max_samples)

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        tour = self.canonical(sol)
        n = len(tour)
        for i in range(n - 1):
            for j in range(i + 1, n):
                yield (i, j)

    def sample(self, sol, k: int, rng: Random) -> list[tuple[int, int]]:
        tour = self.canonical(sol)
        n = len(tour)
        all_moves = [(i, j) for i in range(n - 1) for j in range(i + 1, n)]
        if k >= len(all_moves):
            rng.shuffle(all_moves)
            return all_moves
        return rng.sample(all_moves, k)

    def apply(self, sol, m: tuple[int, int]):
        tour = list(self.canonical(sol))
        i, j = m
        tour[i], tour[j] = tour[j], tour[i]
        return self.canonical(tuple(tour))

    def delta(self, sol, m: tuple[int, int]) -> float:
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))


def build_component(problem, max_samples: int = 15):
    return GiantTourSwapNeighborhood(problem, max_samples=max_samples)
