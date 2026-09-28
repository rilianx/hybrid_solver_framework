from __future__ import annotations

from typing import Any

from generated.cvrp_routes_cycle2.model.parts import _Partial  # type: ignore


COMPONENT = {
    "name": "depot_balance_lookahead",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "start_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
        "route_growth_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DepotBalanceLookahead:
    """CVRP: combina cercanía al depósito con una idea de balance espacial simple.
    Prefiere clientes que no solo son cercanos al depot sino que además están más
    'centrados' respecto al último cliente de la ruta, para evitar rutas zigzagueantes.
    Menor puntaje = mejor."""

    def __init__(self, problem, start_weight: float = 0.8, balance_weight: float = 0.6, route_growth_weight: float = 0.2):
        self.inst = problem.inst
        self.start_weight = float(start_weight)
        self.balance_weight = float(balance_weight)
        self.route_growth_weight = float(route_growth_weight)

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)

        if isinstance(partial, _Partial):
            current = partial.current
        else:
            current = getattr(partial, "current", tuple())

        depot_dist = float(inst.dist(0, c))

        if current:
            last = int(current[-1])
            last_dist = float(inst.dist(last, c))
            # Balanceo: penaliza saltos muy grandes respecto a la referencia del depósito.
            balance = abs(last_dist - depot_dist)
            route_len = float(len(current))
        else:
            last_dist = depot_dist
            balance = 0.0
            route_len = 0.0

        return self.start_weight * depot_dist + self.balance_weight * balance + self.route_growth_weight * route_len


def build_component(problem, start_weight: float = 0.8, balance_weight: float = 0.6, route_growth_weight: float = 0.2):
    return DepotBalanceLookahead(
        problem,
        start_weight=start_weight,
        balance_weight=balance_weight,
        route_growth_weight=route_growth_weight,
    )
