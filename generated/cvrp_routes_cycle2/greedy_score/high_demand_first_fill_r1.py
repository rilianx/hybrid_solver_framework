from __future__ import annotations

from typing import Any

from generated.cvrp_routes_cycle2.model.parts import _Partial  # type: ignore


COMPONENT = {
    "name": "high_demand_first_fill",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "demand_weight": {"type": "float", "range": [0.0, 10.0]},
        "residual_capacity_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class HighDemandFirstFill:
    """CVRP: favorece clientes con mayor demanda para consolidar rutas y reducir el número
    de retornos al depósito. Penaliza decisiones que dejan poca capacidad residual.
    Menor puntaje = mejor."""

    def __init__(self, problem, demand_weight: float = 1.0, residual_capacity_weight: float = 0.3):
        self.inst = problem.inst
        self.demand_weight = float(demand_weight)
        self.residual_capacity_weight = float(residual_capacity_weight)

    def score(self, partial, action) -> float:
        inst = self.inst
        c = int(action)
        demand = float(inst.demand[c])

        if isinstance(partial, _Partial):
            current = partial.current
        else:
            current = getattr(partial, "current", tuple())

        if current:
            load = 0.0
            for i in current:
                load += float(inst.demand[int(i)])
        else:
            load = 0.0

        residual_after = float(inst.capacity) - (load + demand)
        if residual_after < 0.0:
            residual_after = 0.0

        # Mayor demanda => menor score; menor residual => menor score (más "llenar" la ruta).
        return -self.demand_weight * demand - self.residual_capacity_weight * (1.0 / (1.0 + residual_after))


def build_component(problem, demand_weight: float = 1.0, residual_capacity_weight: float = 0.3):
    return HighDemandFirstFill(problem, demand_weight=demand_weight, residual_capacity_weight=residual_capacity_weight)
