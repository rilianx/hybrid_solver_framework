from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial

COMPONENT = {
    "name": "earliness_holding_tradeoff",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "holding_weight": {"type": "float", "range": [0.0, 5.0]},
        "urgency_weight": {"type": "float", "range": [0.0, 5.0]},
        "setup_weight": {"type": "float", "range": [0.0, 5.0]},
        "free_capacity_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class EarlinessHoldingTradeoff:
    """Greedy score para CLSP.

    La acción cubre demanda del ítem `item` con producción en `source` para el período
    `period`. Menor puntaje = mejor.

    Idea:
    - penaliza el costo de adelantar producción: holding incremental ≈ qty * h[i] * (period-source)
    - premia cubrir antes la demanda más urgente (períodos tempranos)
    - favorece usar capacidad libre abundante y, en especial, fuentes ya abiertas
    """

    def __init__(
        self,
        problem,
        holding_weight: float = 1.0,
        urgency_weight: float = 1.0,
        setup_weight: float = 0.4,
        free_capacity_weight: float = 0.3,
    ):
        self.inst: CLSPInstance = problem.inst
        self.holding_weight = holding_weight
        self.urgency_weight = urgency_weight
        self.setup_weight = setup_weight
        self.free_capacity_weight = free_capacity_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        i = action.item
        t = action.period
        s = action.source
        qty = action.qty

        h = self.inst.holding_cost[i]
        st = self.inst.setup_time[i]

        # Costo de adelantar: producir en s y mantener hasta t.
        holding_cost = qty * h * max(t - s, 0)

        # Urgencia: cuanto más temprano es el período cubierto, mayor bonificación.
        # Se normaliza con el horizonte para mantener escalas estables.
        urgency_bonus = qty * h / (1.0 + float(t))

        # Preferir fuentes ya abiertas: si el setup ya existe, no penalizamos; si no,
        # añadimos una pequeña penalización proporcional al tiempo de setup.
        setup_penalty = 0.0 if partial.setup[i][s] else st

        # Capacidad libre: cuando el período fuente está holgado, se favorece más.
        free = partial.free(s)
        cap = self.inst.capacity[s]
        free_ratio = free / max(cap, 1e-9)
        free_bonus = free_ratio * qty

        # Si el source ya está abierto, la solución es más atractiva: pequeña rebaja extra.
        open_bonus = 0.25 * qty if partial.setup[i][s] else 0.0

        return (
            self.holding_weight * holding_cost
            - self.urgency_weight * urgency_bonus
            + self.setup_weight * setup_penalty
            - self.free_capacity_weight * free_bonus
            - open_bonus
        )


def build_component(
    problem,
    holding_weight: float = 1.0,
    urgency_weight: float = 1.0,
    setup_weight: float = 0.4,
    free_capacity_weight: float = 0.3,
):
    return EarlinessHoldingTradeoff(
        problem,
        holding_weight=holding_weight,
        urgency_weight=urgency_weight,
        setup_weight=setup_weight,
        free_capacity_weight=free_capacity_weight,
    )
