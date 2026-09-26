from random import Random
from typing import Any

COMPONENT = {
    "name": "arc_cut_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class ArcCutDestruction:
    """Libera un corte de arcos entre un conjunto de clientes y el resto."""

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

        target = max(1, int(round(ratio * len(customers))))
        seed = rng.choice(customers)
        subset = {seed}

        # Expand subset using nearest-neighbor criterion until target customers
        remaining = [c for c in customers if c != seed]
        remaining.sort(key=lambda c: float(self.inst.dist(seed, c)))
        for c in remaining:
            if len(subset) >= target:
                break
            subset.add(c)

        free_vars: set[str] = set()
        subset_set = set(subset)
        n = self.inst.n_customers

        # Free arcs crossing the cut and depot connections of subset
        for i in range(n + 1):
            for j in range(n + 1):
                if i == j:
                    continue
                in_i = i in subset_set
                in_j = j in subset_set
                if in_i != in_j:
                    free_vars.add(self._x(i, j))

        if not free_vars:
            c = seed
            for i in range(n + 1):
                if i != c:
                    free_vars.add(self._x(i, c))
                    free_vars.add(self._x(c, i))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return ArcCutDestruction(problem)
