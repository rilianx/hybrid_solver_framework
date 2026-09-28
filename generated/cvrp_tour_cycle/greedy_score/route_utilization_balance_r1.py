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
    """CVRP gran tour: busca rutas bien cargadas y equilibradas.
    No solo mira el incremento de distancia, sino también cuán cerca deja la ruta de una
    utilización 'sana' de la capacidad para evitar demasiadas rutas cortas.
    Menor puntaje = mejor."""

    def __init__(self, problem, distance_weight: float = 1.0, utilization_weight: float = 1.0, open_route_penalty: float = 0.3):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.utilization_weight = float(utilization_weight)
        self.open_route_penalty = float(open_route_penalty)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        cap = float(self.inst.capacity)
        load = sum(self.inst.demand[c] for c in open_route)

        if kind == "add":
            c = int(action[1])
            d = float(self.inst.demand[c])

            if not open_route:
                delta = 2.0 * self.inst.dist(0, c)
            else:
                last = open_route[-1]
                delta = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)

            new_load = load + d
            utilization = new_load / max(cap, 1e-9)
            # Target a moderate-high fill: routes that are too empty are penalized.
            target = 0.85
            fill_penalty = abs(target - utilization)
            return self.distance_weight * delta + self.utilization_weight * fill_penalty

        if kind == "close":
            # Closing a nearly empty route is bad; closing a well-utilized route is good.
            fill = load / max(cap, 1e-9)
            return self.open_route_penalty * (1.0 - fill)

        return inf


def build_component(problem, distance_weight: float = 1.0, utilization_weight: float = 1.0, open_route_penalty: float = 0.3):
    return RouteUtilizationBalance(
        problem,
        distance_weight=distance_weight,
        utilization_weight=utilization_weight,
        open_route_penalty=open_route_penalty,
    )
