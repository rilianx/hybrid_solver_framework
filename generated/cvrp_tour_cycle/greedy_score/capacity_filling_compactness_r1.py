from __future__ import annotations

from math import inf
from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "capacity_filling_compactness",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
        "compactness_weight": {"type": "float", "range": [0.0, 10.0]},
        "route_restart_penalty": {"type": "float", "range": [0.0, 5.0]},
    },
}


class CapacityFillingCompactness:
    """CVRP gran tour: busca saturar la ruta abierta con clientes que encajen bien.
    Combina uso de capacidad, cercanía mutua al último nodo y compacidad radial
    respecto al depósito. Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        fill_weight: float = 2.0,
        compactness_weight: float = 0.5,
        route_restart_penalty: float = 0.25,
    ):
        self.inst = problem.inst
        self.fill_weight = fill_weight
        self.compactness_weight = compactness_weight
        self.route_restart_penalty = route_restart_penalty

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            if not open_route:
                return inf
            load = 0.0
            for c in open_route:
                load += float(self.inst.demand[c])
            cap = max(float(self.inst.capacity), 1e-9)
            fill_ratio = load / cap
            # Cerrar es más atractivo si la ruta está bien cargada.
            return self.route_restart_penalty + (1.0 - fill_ratio)

        c = int(action[1])
        demand_c = float(self.inst.demand[c])
        depot_dist = float(self.inst.dist(0, c))

        if not open_route:
            # Si no hay ruta abierta, preferir arrancar con clientes "centrales" y demandantes.
            return depot_dist - self.fill_weight * demand_c + self.compactness_weight * depot_dist

        last = open_route[-1]
        add_cost = float(self.inst.dist(last, c))
        return_to_depot = float(self.inst.dist(c, 0))
        keep_route_cost = add_cost + return_to_depot - float(self.inst.dist(last, 0))

        load = 0.0
        for x in open_route:
            load += float(self.inst.demand[x])
        remaining_cap = max(float(self.inst.capacity) - load, 0.0)

        fit_slack = max(0.0, remaining_cap - demand_c)
        compactness = depot_dist + return_to_depot
        return keep_route_cost + self.compactness_weight * compactness + 0.05 * fit_slack - self.fill_weight * demand_c


def build_component(
    problem,
    fill_weight: float = 2.0,
    compactness_weight: float = 0.5,
    route_restart_penalty: float = 0.25,
):
    return CapacityFillingCompactness(
        problem,
        fill_weight=fill_weight,
        compactness_weight=compactness_weight,
        route_restart_penalty=route_restart_penalty,
    )
