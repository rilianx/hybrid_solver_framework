from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "earliest_deadline_setup_aware",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "deadline_weight": {"type": "float", "range": [0.0, 5.0]},
        "holding_weight": {"type": "float", "range": [0.0, 5.0]},
        "source_distance_weight": {"type": "float", "range": [0.0, 5.0]},
        "setup_bonus_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class EarliestDeadlineSetupAware:
    """Puntúa acciones que cubren antes lo más urgente, favoreciendo fuentes cercanas.

    Menor puntaje = mejor. La idea es:
    - priorizar el período objetivo más temprano;
    - penalizar más la producción desde fuentes lejanas al deadline, porque suele generar inventario;
    - penalizar el uso de ítems caros de mantener en inventario;
    - bonificar que no requiera un nuevo setup.
    """

    def __init__(
        self,
        problem,
        deadline_weight: float = 1.0,
        holding_weight: float = 1.0,
        source_distance_weight: float = 0.5,
        setup_bonus_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.deadline_weight = deadline_weight
        self.holding_weight = holding_weight
        self.source_distance_weight = source_distance_weight
        self.setup_bonus_weight = setup_bonus_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source
        h = inst.holding_cost[i]

        deadline_term = self.deadline_weight * float(t)
        holding_term = self.holding_weight * h * float(t - s)
        distance_term = self.source_distance_weight * float(t - s)
        setup_term = -self.setup_bonus_weight * (1.0 if not action.new_setup else 0.0)

        # Pequeño sesgo hacia acciones más grandes, para vaciar antes la demanda crítica.
        qty_term = -1e-6 * float(action.qty)

        return deadline_term + holding_term + distance_term + setup_term + qty_term


def build_component(problem, deadline_weight: float = 1.0, holding_weight: float = 1.0,
                    source_distance_weight: float = 0.5, setup_bonus_weight: float = 1.0):
    return EarliestDeadlineSetupAware(
        problem,
        deadline_weight=deadline_weight,
        holding_weight=holding_weight,
        source_distance_weight=source_distance_weight,
        setup_bonus_weight=setup_bonus_weight,
    )
