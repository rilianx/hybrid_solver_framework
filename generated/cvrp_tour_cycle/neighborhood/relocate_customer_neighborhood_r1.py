from __future__ import annotations

from random import Random
from typing import Iterable

from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "relocate_customer_neighborhood",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "sample_size": {"type": "int", "range": [1, 100]},
    },
}


class RelocateCustomerNeighborhood:
    """Mueve un cliente a otra posición del tour. Movimiento = (i, j), insertar i en j."""

    def __init__(self, problem, sample_size: int = 20):
        self.problem = problem
        self.sample_size = int(sample_size)

    def moves(self, sol) -> Iterable[tuple[int, int]]:
        tour = canonical(sol)
        n = len(tour)
        for i in range(n):
            for j in range(n):
                if i != j:
                    yield (i, j)

    def sample(self, sol, k: int, rng: Random) -> list[tuple[int, int]]:
        tour = canonical(sol)
        n = len(tour)
        all_moves = [(i, j) for i in range(n) for j in range(n) if i != j]
        if not all_moves or k <= 0:
            return []
        k = min(k, len(all_moves))
        return rng.sample(all_moves, k)

    def apply(self, sol, m) -> tuple[int, ...]:
        tour = list(canonical(sol))
        i, j = m
        if i == j:
            return canonical(tuple(tour))
        c = tour.pop(i)
        if j > i:
            j -= 1
        tour.insert(j, c)
        return canonical(tuple(tour))

    def undo(self, sol, m) -> tuple[int, ...]:
        tour = list(canonical(sol))
        i, j = m
        if i == j:
            return canonical(tuple(tour))
        c = tour.pop(j if j < i else j - 1)
        tour.insert(i, c)
        return canonical(tuple(tour))

    def delta(self, sol, m) -> float:
        return float(self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))


def build_component(problem, **params):
    sample_size = params.get("sample_size", 20)
    return RelocateCustomerNeighborhood(problem, sample_size=sample_size)
