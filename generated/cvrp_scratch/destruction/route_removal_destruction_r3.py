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
    """Elimina rutas completas o, si hace falta, segmentos dentro de la ruta más cargada."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _route_demand(self, route):
        return sum(self.inst.demand[c] for c in route)

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

        # Prefer removing complete routes: this is structurally different from
        # customer-by-customer destruction and exploits the route partition.
        route_info = []
        for r in routes:
            route_info.append((len(r), self._route_demand(r), r))
        route_info.sort(key=lambda t: (t[1], t[0]), reverse=True)

        removed = set()
        for _, _, route in route_info:
            if len(removed) >= target:
                break
            if len(removed) + len(route) <= target:
                removed.update(route)

        # If we still need more customers, remove a contiguous block from the
        # most loaded remaining route, centered around its highest-demand client.
        if len(removed) < target:
            remaining_routes = [r for r in routes if any(c not in removed for c in r)]
            if remaining_routes:
                remaining_routes.sort(
                    key=lambda r: (self._route_demand(r), len(r)), reverse=True
                )
                seed_route = remaining_routes[0]
                # Seed at the customer with maximum demand on that route.
                seed_pos = max(
                    range(len(seed_route)),
                    key=lambda p: (self.inst.demand[seed_route[p]], -p),
                )
                left = right = seed_pos
                if seed_route[seed_pos] not in removed:
                    removed.add(seed_route[seed_pos])

                # Expand contiguously within the same route.
                while len(removed) < target and (left > 0 or right + 1 < len(seed_route)):
                    can_left = left > 0 and seed_route[left - 1] not in removed
                    can_right = right + 1 < len(seed_route) and seed_route[right + 1] not in removed
                    if can_left and can_right:
                        # Bias toward the side with higher cumulative demand nearby.
                        left_score = self.inst.demand[seed_route[left - 1]]
                        right_score = self.inst.demand[seed_route[right + 1]]
                        if right_score > left_score or (right_score == left_score and rng.random() < 0.5):
                            right += 1
                            removed.add(seed_route[right])
                        else:
                            left -= 1
                            removed.add(seed_route[left])
                    elif can_left:
                        left -= 1
                        removed.add(seed_route[left])
                    elif can_right:
                        right += 1
                        removed.add(seed_route[right])
                    else:
                        break

        free_vars = set()
        for i in removed:
            for j in range(0, n_customers + 1):
                if i != j:
                    free_vars.add(var_name(i, j))
                    free_vars.add(var_name(j, i))

        if not free_vars:
            free_vars.add(next(iter(assignment)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = params.get("ratio", 0.25)
    return RouteRemovalDestruction(problem, problem.inst)
