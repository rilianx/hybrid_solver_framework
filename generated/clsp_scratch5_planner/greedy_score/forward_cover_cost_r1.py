from __future__ import annotations

from typing import Protocol, runtime_checkable


COMPONENT = {
    "name": "forward_cover_cost",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "holding_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class ForwardCoverCost:
    """CLSP: puntúa una acción de cobertura por su costo marginal inmediato.

    Menor puntaje es mejor. La acción cubre `qty` unidades de la demanda
    `(item, period)` produciendo en `source <= period`.

    Idea:
    - si hace falta, paga el setup del ítem en `source`;
    - añade el costo de inventario por anticipar la producción desde `source`
      hasta `period`;
    - normaliza por la cantidad cubierta para favorecer coberturas urgentes
      con bajo sacrificio local.
    """

    def __init__(self, problem, holding_weight: float = 1.0):
        self.inst = problem.inst
        self.holding_weight = holding_weight

    def score(self, partial, action):
        i = action.item
        t = action.period
        s = action.source
        qty = action.qty

        setup_cost = self.inst.setup_cost[i] if action.new_setup else 0.0
        holding_cost = self.inst.holding_cost[i] * max(0, t - s) * qty
        total = setup_cost + self.holding_weight * holding_cost
        return total / max(qty, 1e-12)


def build_component(problem, holding_weight: float = 1.0):
    return ForwardCoverCost(problem, holding_weight=holding_weight)
