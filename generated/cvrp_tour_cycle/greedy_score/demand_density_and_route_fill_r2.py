from __future__ import annotations

import math
from typing import Any


COMPONENT = {
    "name": "demand_density_and_route_fill",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "capacity_weight": {"type": "float", "range": [0.0, 10.0]},
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DemandDensityAndRouteFill:
    """CVRP con gran tour: puntúa acciones por ajuste de carga a una meta de empaquetado
    derivada del remanente, con un pequeño sesgo geométrico. Menor puntaje = mejor.

    La idea algorítmica es distinta de una extensión puramente cercana al último cliente:
    aquí se usa la estructura global de demanda restante para favorecer elecciones que
    dejen el remanente "empaquetable" en menos rutas y con cargas más equilibradas.
    """

    def __init__(
        self,
        problem,
        capacity_weight: float = 1.0,
        distance_weight: float = 1.0,
        fill_weight: float = 1.0,
    ):
        self.inst = problem.inst
        self.capacity_weight = float(capacity_weight)
        self.distance_weight = float(distance_weight)
        self.fill_weight = float(fill_weight)

    def _demand(self, c: int) -> float:
        return float(self.inst.demand[c])

    def _dist(self, i: int, j: int) -> float:
        return float(self.inst.dist(i, j))

    def _remaining_stats(self, remaining: Any, cap: float) -> tuple[float, float]:
        rem_demand = 0.0
        rem_count = 0
        try:
            for c in remaining:
                rem_demand += self._demand(int(c))
                rem_count += 1
        except TypeError:
            # Fallback in case remaining is not directly iterable, though it should be.
            return 0.0, 0.0

        if rem_count <= 0 or cap <= 0.0:
            return rem_demand, 0.0

        # If we have total remaining demand, estimate a target load per future route.
        future_routes = max(1.0, math.ceil(rem_demand / cap))
        target_load = rem_demand / future_routes
        return rem_demand, target_load

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)
        eps = 1e-9

        rem_demand, target_load = self._remaining_stats(remaining, cap)

        if kind == "close":
            if not open_route:
                return 0.0

            load = 0.0
            for c in open_route:
                load += self._demand(int(c))

            # Prefer closing when the current route is close to the target load implied
            # by the remaining demand distribution. This is a packing criterion, not
            # a geometric nearest-neighbor criterion.
            if target_load > 0.0:
                load_gap = abs(load - target_load) / max(cap, eps)
            else:
                load_gap = abs(load - cap) / max(cap, eps)

            fill_ratio = load / max(cap, eps)
            slack_ratio = max(0.0, cap - load) / max(cap, eps)

            # Small bias toward fuller routes, but the main signal is the packability gap.
            return (
                self.fill_weight * (0.75 * load_gap + 0.25 * slack_ratio)
                - 0.05 * self.fill_weight * fill_ratio
            )

        c = int(action[1])
        demand = self._demand(c)

        # If no route is open, prefer customers whose demand better anchors a future route
        # with respect to the remaining demand profile; use distance only as a minor tie-breaker.
        if not open_route:
            depot_dist = self._dist(0, c)
            if target_load > 0.0:
                anchor_gap = abs(demand - target_load) / max(cap, eps)
            else:
                anchor_gap = demand / max(cap, eps)

            density = demand / max(depot_dist, eps)
            return (
                self.fill_weight * anchor_gap
                + self.distance_weight * (depot_dist / max(cap, eps))
                - self.capacity_weight * density
            )

        last = int(open_route[-1])
        current_load = 0.0
        for x in open_route:
            current_load += self._demand(int(x))

        new_load = current_load + demand
        if target_load > 0.0:
            new_gap = abs(new_load - target_load) / max(cap, eps)
        else:
            new_gap = abs(cap - new_load) / max(cap, eps)

        # Geometric term is only a tie-breaker: we care mostly about how this choice
        # positions the route against the remaining demand profile.
        detour = self._dist(last, c) + self._dist(c, 0) - self._dist(last, 0)
        detour_term = detour / max(cap, eps)

        # Penalize choices that overshoot the effective packing target and reward
        # those that use capacity in a way that helps future route packing.
        fill_ratio = min(new_load / max(cap, eps), 1.0)
        overshoot = max(0.0, new_load - cap) / max(cap, eps)

        density = demand / max(detour + eps, eps)
        return (
            self.fill_weight * (0.8 * new_gap + 0.2 * overshoot)
            + self.distance_weight * detour_term
            - self.capacity_weight * density
            - 0.05 * self.fill_weight * fill_ratio
        )


def build_component(
    problem,
    capacity_weight: float = 1.0,
    distance_weight: float = 1.0,
    fill_weight: float = 1.0,
):
    return DemandDensityAndRouteFill(
        problem,
        capacity_weight=capacity_weight,
        distance_weight=distance_weight,
        fill_weight=fill_weight,
    )
