from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import var_name

COMPONENT = {
    "name": "route_removal_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteRemovalDestruction:
    """Elimina un tramo contiguo de una ruta semilla y, si hace falta, clientes cercanos."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _build_customer_index(self, sol):
        pos = {}
        for r_idx, route in enumerate(sol):
            for p_idx, c in enumerate(route):
                pos[c] = (r_idx, p_idx)
        return pos

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = [tuple(r) for r in sol if r]
        if not routes:
            return assignment, set()

        n_customers = self.inst.n_customers
        target = max(1, int(round(ratio * n_customers)))

        # Choose a seed customer from a longer route to create a contiguous destruction block.
        route_weights = [len(r) for r in routes]
        seed_route = rng.choices(routes, weights=route_weights, k=1)[0]
        seed_pos = rng.randrange(len(seed_route))
        seed_customer = seed_route[seed_pos]

        removed = set()

        # First: remove a contiguous segment around the seed inside its route.
        left = seed_pos
        right = seed_pos
        removed.add(seed_customer)

        # Expand contiguously, alternating sides randomly, until target or route exhausted.
        while len(removed) < target and (left > 0 or right + 1 < len(seed_route)):
            can_left = left > 0
            can_right = right + 1 < len(seed_route)
            if can_left and can_right:
                if rng.random() < 0.5:
                    left -= 1
                    removed.add(seed_route[left])
                else:
                    right += 1
                    removed.add(seed_route[right])
            elif can_left:
                left -= 1
                removed.add(seed_route[left])
            else:
                right += 1
                removed.add(seed_route[right])

        # Second: if quota remains, remove geographically close customers to the seed,
        # preferably from other routes to diversify the destruction.
        if len(removed) < target:
            seed_x, seed_y = self.inst.coords[seed_customer]
            customer_positions = self._build_customer_index(sol)

            candidates = [c for c in range(1, n_customers + 1) if c not in removed]
            candidates.sort(
                key=lambda c: (
                    0 if customer_positions.get(c, (None, None))[0] != customer_positions[seed_customer][0] else 1,
                    self.inst.dist(seed_customer, c),
                )
            )

            for c in candidates:
                removed.add(c)
                if len(removed) >= target:
                    break

        free_vars = set()
        for i in removed:
            for j in range(0, n_customers + 1):
                if i != j:
                    free_vars.add(var_name(i, j))
                    free_vars.add(var_name(j, i))

        if not free_vars:
            # Fallback: free one customer-related arc if the instance is degenerate.
            free_vars.add(next(iter(assignment)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = params.get("ratio", 0.25)
    return RouteRemovalDestruction(problem, problem.inst)
