from __future__ import annotations

from math import inf
from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "radial_demand_balance_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "radial_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
        "close_empty_penalty": {"type": "float", "range": [0.0, 10.0]},
    },
}


class RadialDemandBalanceScore:
    """CVRP gran tour: favorece clientes que están radialmente cerca del depósito
    pero también "equilibran" la carga. La idea es construir rutas con clientes
    relativamente próximos al depot y con demanda que use bien la capacidad.
    Menor puntaje = mejor."""

    def __init__(
        self,
        problem,
        radial_weight: float = 1.0,
        balance_weight: float = 1.0,
        close_empty_penalty: float = 3.0,
    ):
        self.inst = problem.inst
        self.radial_weight = radial_weight
        self.balance_weight = balance_weight
        self.close_empty_penalty = close_empty_penalty

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            if not open_route:
                return inf
            # Cerrar temprano es malo si aún queda mucha capacidad libre.
            load = 0.0
            for c in open_route:
                load += float(self.inst.demand[c])
            cap = max(float(self.inst.capacity), 1e-9)
            unused = max(cap - load, 0.0) / cap
            return self.close_empty_penalty * unused

        c = int(action[1])
        demand_c = float(self.inst.demand[c])
        radial = float(self.inst.dist(0, c))

        if not open_route:
            # Arrancar la primera ruta con nodos poco costosos de ida/vuelta,
            # pero premiando demandas mayores para no desperdiciar vehículos.
            return self.radial_weight * radial - self.balance_weight * (demand_c / max(float(self.inst.capacity), 1e-9))

        last = open_route[-1]
        marginal = float(self.inst.dist(last, c)) + float(self.inst.dist(c, 0)) - float(self.inst.dist(last, 0))

        load = 0.0
        for x in open_route:
            load += float(self.inst.demand[x])
        cap = max(float(self.inst.capacity), 1e-9)
        fill = load / cap
        demand_fill_gap = abs((load + demand_c) - 0.5 * cap) / cap

        return marginal + self.radial_weight * radial + self.balance_weight * demand_fill_gap - 0.5 * fill


def build_component(
    problem,
    radial_weight: float = 1.0,
    balance_weight: float = 1.0,
    close_empty_penalty: float = 3.0,
):
    return RadialDemandBalanceScore(
        problem,
        radial_weight=radial_weight,
        balance_weight=balance_weight,
        close_empty_penalty=close_empty_penalty,
    )
