from __future__ import annotations

from typing import Any

from generated.cvrp_routes_cycle2.model.parts import _Partial  # type: ignore


COMPONENT = {
    "name": "nearest_next_customer",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "distance_weight": {"type": "float", "range": [0.0, 10.0]},
        "depot_bias": {"type": "float", "range": [0.0, 10.0]},
    },
}


class NearestNextCustomer:
    """CVRP: favorece continuar la ruta con el cliente más cercano al último nodo visitado.
    Si no hay ruta abierta, prioriza clientes cercanos al depósito. Menor puntaje = mejor."""

    def __init__(self, problem, distance_weight: float = 1.0, depot_bias: float = 0.2):
        self.inst = problem.inst
        self.distance_weight = float(distance_weight)
        self.depot_bias = float(depot_bias)

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)

        if isinstance(partial, _Partial):
            current = partial.current
        else:
            current = getattr(partial, "current", tuple())

        if current:
            last = int(current[-1])
            route_dist = float(inst.dist(last, c))
        else:
            route_dist = float(inst.dist(0, c))

        depot_dist = float(inst.dist(0, c))
        return self.distance_weight * route_dist + self.depot_bias * depot_dist


def build_component(problem, distance_weight: float = 1.0, depot_bias: float = 0.2):
    return NearestNextCustomer(problem, distance_weight=distance_weight, depot_bias=depot_bias)
