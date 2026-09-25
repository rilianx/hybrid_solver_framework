from __future__ import annotations

from math import inf
from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial

COMPONENT = {
    "name": "amortized_unit_cost",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "setup_weight": {"type": "float", "range": [0.0, 5.0]},
        "inventory_weight": {"type": "float", "range": [0.0, 5.0]},
        "existing_setup_bonus": {"type": "float", "range": [0.0, 5.0]},
    },
}


class AmortizedUnitCost:
    """Puntúa por costo unitario amortizado: setup + inventario esperado por unidad.

    Menor es mejor. Favorece:
    - usar un setup ya encendido en `source`;
    - cubrir demandas baratas en términos de setup por unidad;
    - evitar adelantar demasiado producción cuando el holding es alto.
    """

    def __init__(
        self,
        problem,
        setup_weight: float = 1.0,
        inventory_weight: float = 1.0,
        existing_setup_bonus: float = 0.5,
    ):
        self.inst: CLSPInstance = problem.inst
        self.setup_weight = setup_weight
        self.inventory_weight = inventory_weight
        self.existing_setup_bonus = existing_setup_bonus

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        s = action.source
        t = action.period
        q = max(action.qty, 1e-12)

        setup_cost = inst.setup_cost[i] if action.new_setup else 0.0
        setup_term = self.setup_weight * setup_cost / q

        holding_term = 0.0
        if s < t:
            holding_term = self.inventory_weight * inst.holding_cost[i] * (t - s)

        source_load = partial.used[s]
        source_pressure = source_load / max(inst.capacity[s], 1e-12)

        bonus = 0.0
        if partial.setup[i][s]:
            bonus = self.existing_setup_bonus

        return setup_term + holding_term + 0.05 * source_pressure - bonus


def build_component(problem, setup_weight: float = 1.0, inventory_weight: float = 1.0, existing_setup_bonus: float = 0.5):
    return AmortizedUnitCost(problem, setup_weight, inventory_weight, existing_setup_bonus)
