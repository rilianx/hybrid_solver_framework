from __future__ import annotations

from math import inf

COMPONENT = {
    "name": "route_utilization_balance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "utilization_weight": {"type": "float", "range": [0.0, 10.0]},
        "open_route_penalty": {"type": "float", "range": [0.0, 10.0]},
    },
}


class RouteUtilizationBalance:
    """CVRP gran tour: prioriza cortes que produzcan rutas con carga razonablemente
    equilibrada respecto a la demanda restante, además de un sesgo suave por distancia.
    Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        distance_weight: float = 1.0,
        utilization_weight: float = 1.0,
        open_route_penalty: float = 0.3,
    ):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.utilization_weight = float(utilization_weight)
        self.open_route_penalty = float(open_route_penalty)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)

        load = 0.0
        for c in open_route:
            load += float(self.inst.demand[c])

        remaining_demand = 0.0
        for c in remaining:
            remaining_demand += float(self.inst.demand[c])

        if kind == "add":
            c = int(action[1])
            d = float(self.inst.demand[c])

            if not open_route:
                delta = 2.0 * float(self.inst.dist(0, c))
            else:
                last = open_route[-1]
                delta = float(self.inst.dist(last, c)) + float(self.inst.dist(c, 0)) - float(self.inst.dist(last, 0))

            new_load = load + d
            slack = max(cap - new_load, 0.0)

            # Estimate how many routes are still "available" in the remainder if we close now.
            # Prefer fillings that leave a slack consistent with the average remaining demand.
            expected_future_load = remaining_demand
            balance_target = 0.0
            if remaining:
                balance_target = expected_future_load / max(1.0, float(len(remaining)))

            # Penalize emptying too little of the capacity, but also avoid overfilling relative
            # to the average future demand profile.
            utilization_gap = abs(slack - balance_target) / max(cap, 1e-9)

            # Mild preference for keeping the route non-trivially filled.
            underfill_penalty = max(0.0, 0.15 - (new_load / max(cap, 1e-9)))

            return self.distance_weight * delta + self.utilization_weight * (
                utilization_gap + underfill_penalty
            )

        if kind == "close":
            # Closing is attractive when the current route is already well packed.
            fill = load / max(cap, 1e-9)

            # Use the remaining demand to discourage premature closures when the
            # current route is still too small compared to what is left.
            remaining_mean = remaining_demand / max(1.0, float(len(remaining))) if remaining else 0.0
            small_route_penalty = max(0.0, (remaining_mean - load) / max(cap, 1e-9))

            return self.open_route_penalty * (1.0 - fill) + self.utilization_weight * small_route_penalty

        return inf


def build_component(
    problem,
    distance_weight: float = 1.0,
    utilization_weight: float = 1.0,
    open_route_penalty: float = 0.3,
):
    return RouteUtilizationBalance(
        problem,
        distance_weight=distance_weight,
        utilization_weight=utilization_weight,
        open_route_penalty=open_route_penalty,
    )
