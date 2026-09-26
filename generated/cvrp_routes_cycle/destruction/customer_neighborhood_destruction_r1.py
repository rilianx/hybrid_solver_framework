from random import Random
from typing import Any

COMPONENT = {
    "name": "customer_neighborhood_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class CustomerNeighborhoodDestruction:
    """Libera clientes alrededor de un cliente semilla y sus arcos incidentes."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    @staticmethod
    def _x(i: int, j: int) -> str:
        return f"x_{i}_{j}"

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        customers = list(self.inst.customers)
        if not customers:
            key = next(iter(assignment))
            free_vars = {key}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        seed = rng.choice(customers)
        target = max(1, int(round(ratio * len(customers))))

        # score by geometric proximity to seed
        scored = []
        for c in customers:
            if c == seed:
                score = -1.0
            else:
                score = float(self.inst.dist(seed, c))
            scored.append((score, c))
        scored.sort()

        chosen = [c for _, c in scored[:target]]
        chosen_set = set(chosen)

        free_vars: set[str] = set()
        for c in chosen_set:
            for i in range(self.inst.n_customers + 1):
                if i != c:
                    free_vars.add(self._x(i, c))
                    free_vars.add(self._x(c, i))

        if not free_vars:
            c = seed
            for i in range(self.inst.n_customers + 1):
                if i != c:
                    free_vars.add(self._x(i, c))
                    free_vars.add(self._x(c, i))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.25))
    return CustomerNeighborhoodDestruction(problem)
