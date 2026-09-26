from __future__ import annotations

from random import Random
from typing import Any


COMPONENT = {
    "name": "shaw_related_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class ShawRelatedCustomerDestruction:
    """Libera clientes relacionados por proximidad geográfica y demanda, pero dispersándolos sobre el tour."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_all = set(assignment.keys())

        tour = tuple(int(c) for c in sol)
        n = len(tour)
        if n == 0:
            return dict(assignment), set()

        k = max(1, int(round(ratio * n)))
        k = min(k, n)

        seed_pos = rng.randrange(n)
        seed = tour[seed_pos]

        # Relatedness w.r.t. a random seed, but the selection is intentionally
        # spread over the whole tour instead of taking a contiguous block.
        def relatedness(c: int) -> float:
            d = float(self.inst.dist(seed, c))
            dem = abs(float(self.inst.demand[seed]) - float(self.inst.demand[c]))
            return d + 0.1 * dem

        ordered = sorted(tour, key=relatedness)

        # Pick candidates with a stride to avoid contiguity on the tour.
        stride = max(2, n // k) if k < n else 1
        start = rng.randrange(min(stride, len(ordered)))
        chosen_customers = set()
        idx = start
        while len(chosen_customers) < k and ordered:
            chosen_customers.add(ordered[idx % n])
            idx += stride

        # If stride hits duplicates (small n), fill with the remaining most-related customers.
        if len(chosen_customers) < k:
            for c in ordered:
                if len(chosen_customers) >= k:
                    break
                chosen_customers.add(c)

        free_vars = set()

        # Free variables associated with the selected customers.
        # On the MIP view, this typically liberates arcs incident to those customers,
        # but the selected customers are deliberately dispersed by the stride above.
        for v in vars_all:
            if not v.startswith("x_"):
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            if i in chosen_customers or j in chosen_customers:
                free_vars.add(v)

        if not free_vars:
            # Fall back to a non-empty, valid relaxation.
            free_vars.add(next(iter(vars_all)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return ShawRelatedCustomerDestruction(problem)
