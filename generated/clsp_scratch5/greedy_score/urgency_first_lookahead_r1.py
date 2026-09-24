from __future__ import annotations

from typing import Protocol

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "urgency_first_lookahead",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "urgency_weight": {"type": "float", "range": [0.0, 20.0]},
        "source_delay_weight": {"type": "float", "range": [0.0, 5.0]},
        "setup_penalty_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class UrgencyFirstLookahead:
    """Puntúa principalmente por urgencia del período objetivo.

    Idea:
    - cubrir antes las demandas más apremiantes;
    - preferir fuentes más cercanas al deadline;
    - castigar abrir setups innecesarios.
    Este criterio es distinto: ordena por urgencia temporal, no por costo inmediato.
    """

    def __init__(
        self,
        problem,
        urgency_weight: float = 5.0,
        source_delay_weight: float = 0.5,
        setup_penalty_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.urgency_weight = urgency_weight
        self.source_delay_weight = source_delay_weight
        self.setup_penalty_weight = setup_penalty_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i, t, s, q = action.item, action.period, action.source, action.qty

        # Más urgente cuanto menor es t: prioriza deadlines tempranos.
        urgency = t

        # Preferir no adelantar demasiado la producción.
        source_delay = max(0, t - s)

        # Penaliza abrir un setup nuevo, especialmente si el ítem es caro de preparar.
        setup_term = inst.setup_cost[i] if action.new_setup else 0.0

        # Demanda más grande en períodos tempranos se considera más crítica.
        demand_scale = max(inst.demand[i][t], 1.0)

        return (
            self.urgency_weight * urgency / demand_scale
            + self.source_delay_weight * source_delay
            + self.setup_penalty_weight * setup_term / max(q, 1e-9)
        )


def build_component(problem, urgency_weight: float = 5.0, source_delay_weight: float = 0.5, setup_penalty_weight: float = 1.0):
    return UrgencyFirstLookahead(
        problem,
        urgency_weight=urgency_weight,
        source_delay_weight=source_delay_weight,
        setup_penalty_weight=setup_penalty_weight,
    )
