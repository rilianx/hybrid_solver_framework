from __future__ import annotations

from math import inf
from typing import Any

COMPONENT = {
    "name": "cheapest_incremental_distance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "route_open_penalty": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CheapestIncrementalDistance:
    """CVRP gran tour: favorece la acción que menos aumenta la distancia local.
    Para `add`, usa el incremento exacto de insertar el cliente al final de la ruta abierta.
    Para `close`, aplica una pequeña penalización por cerrar una ruta demasiado pronto.
    Menor puntaje = mejor."""

    def __init__(self, problem, distance_weight: float = 1.0, route_open_penalty: float = 0.1):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.route_open_penalty = float(route_open_penalty)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "add":
            c = int(action[1])
            d = self.inst.demand[c]
            if not open_route:
                # Start a new route: depot -> c -> depot.
                delta = 2.0 * self.inst.dist(0, c)
            else:
                last = open_route[-1]
                delta = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)

            # Mild preference for higher-demand customers when the incremental cost is similar.
            urgency = d / max(float(self.inst.capacity), 1e-9)
            return self.distance_weight * delta - 0.01 * urgency

        if kind == "close":
            # Closing is a fallback; discourage it only slightly when the route is short.
            route_len = len(open_route)
            return self.route_open_penalty / (1.0 + route_len)

        return inf


def build_component(problem, distance_weight: float = 1.0, route_open_penalty: float = 0.1):
    return CheapestIncrementalDistance(problem, distance_weight=distance_weight, route_open_penalty=route_open_penalty)
