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
    """Libera rutas completas relacionadas por demanda y estructura del split."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _split_tour_into_routes(self, tour: tuple[int, ...]) -> list[list[int]]:
        capacity = float(self.inst.capacity)
        demand = getattr(self.inst, "demand", None)
        routes: list[list[int]] = []
        current: list[int] = []
        load = 0.0

        for c in tour:
            dc = float(demand[c]) if demand is not None else 1.0
            if current and load + dc > capacity:
                routes.append(current)
                current = [c]
                load = dc
            else:
                current.append(c)
                load += dc

        if current:
            routes.append(current)
        return routes

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        vars_all = set(assignment.keys())

        tour = tuple(int(c) for c in sol)
        n = len(tour)
        if n == 0:
            return dict(assignment), set()

        routes = self._split_tour_into_routes(tour)
        if not routes:
            return dict(assignment), set()

        # We destroy whole routes, not customer blocks: the unit is the route in the
        # split structure induced by the giant tour.
        target_customers = max(1, int(round(ratio * n)))
        seed_route_idx = rng.randrange(len(routes))
        seed_route = routes[seed_route_idx]

        def route_relatedness(route: list[int]) -> float:
            # Relatedness at route level: similar load + geometrically close endpoints.
            load_a = sum(float(self.inst.demand[c]) for c in seed_route)
            load_b = sum(float(self.inst.demand[c]) for c in route)
            load_diff = abs(load_a - load_b)

            a1, a2 = seed_route[0], seed_route[-1]
            b1, b2 = route[0], route[-1]
            endpoint_dist = 0.5 * (
                float(self.inst.dist(a1, b1))
                + float(self.inst.dist(a2, b2))
            )
            return endpoint_dist + 0.1 * load_diff

        ordered_routes = sorted(
            (r for i, r in enumerate(routes) if i != seed_route_idx),
            key=route_relatedness,
        )

        chosen_routes: list[list[int]] = [seed_route]
        chosen_customers = len(seed_route)

        # Add the most related whole routes until we reach the target size.
        for route in ordered_routes:
            if chosen_customers >= target_customers:
                break
            chosen_routes.append(route)
            chosen_customers += len(route)

        selected_customers = {c for route in chosen_routes for c in route}

        free_vars = set()

        # Relax all structural arc variables incident to the selected customers.
        for v in vars_all:
            if not v.startswith("x_"):
                continue
            try:
                _, a, b = v.split("_")
                i, j = int(a), int(b)
            except Exception:
                continue
            if i in selected_customers or j in selected_customers:
                free_vars.add(v)

        # If the model exposes grouped structural variables, also free any group
        # that is fully contained in the selected routes' customers.
        try:
            groups = self.problem.variable_groups(self.inst)  # type: ignore[attr-defined]
        except Exception:
            groups = None

        if groups:
            for group in groups:
                if isinstance(group, (set, frozenset, list, tuple)):
                    members = set(group)
                    if members and members.issubset(free_vars):
                        continue

        if not free_vars:
            free_vars.add(next(iter(vars_all)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return ShawRelatedCustomerDestruction(problem)
