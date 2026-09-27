from __future__ import annotations

from math import inf
from generated.cvrp_tour_cycle.model.parts import canonical


COMPONENT = {
    "name": "nearest_insertion_with_close_bias",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "close_bias": {"type": "float", "range": [0.0, 10.0]},
        "demand_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class NearestInsertionWithCloseBias:
    """CVRP gran tour: prioriza el cliente que cause menor incremento marginal
    en la ruta abierta. Si la acción es cerrar, la penaliza/bonifica según cuánto
    conviene cortar la ruta actual. Menor puntaje = mejor."""

    def __init__(self, problem, close_bias: float = 1.0, demand_weight: float = 0.25):
        self.inst = problem.inst
        self.close_bias = close_bias
        self.demand_weight = demand_weight

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            if not open_route:
                return inf
            # Cerrar es bueno si la ruta ya está "suficientemente llena".
            load = 0.0
            for c in open_route:
                load += self.inst.demand[c]
            fill = load / max(float(self.inst.capacity), 1e-9)
            return self.close_bias * (1.0 - fill)

        c = int(action[1])
        d = float(self.inst.demand[c])

        if not open_route:
            # Iniciar una ruta: favorece clientes cercanos al depósito y con demanda alta.
            return self.inst.dist(0, c) - self.demand_weight * d

        last = open_route[-1]
        delta = self.inst.dist(last, c) + self.inst.dist(c, 0) - self.inst.dist(last, 0)

        # Penaliza más si el cliente queda "lejano" del extremo actual.
        depot_pull = self.inst.dist(0, c)
        return delta + 0.1 * depot_pull - self.demand_weight * d


def build_component(problem, close_bias: float = 1.0, demand_weight: float = 0.25):
    return NearestInsertionWithCloseBias(problem, close_bias=close_bias, demand_weight=demand_weight)
