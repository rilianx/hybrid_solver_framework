from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "setup_consolidation_urgency",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "future_window": {"type": "int", "range": [1, 12]},
        "setup_bias": {"type": "float", "range": [0.0, 10.0]},
        "consolidation_weight": {"type": "float", "range": [0.0, 10.0]},
        "holding_weight": {"type": "float", "range": [0.0, 10.0]},
        "same_setup_bonus": {"type": "float", "range": [0.0, 10.0]},
    },
}


class SetupConsolidationUrgency:
    """CLSP: puntúa cubrir demanda favoreciendo la consolidación temporal por ítem.

    Menor score = mejor.

    Idea:
    - Si la acción usa un `source` con setup ya activo para el ítem, la premia.
    - Si abre un setup nuevo, la penaliza más cuando la demanda futura cercana del
      mismo ítem es pequeña, porque ese setup corre el riesgo de quedar "aislado".
    - Favorece acciones que cubren más demanda pendiente del ítem (especialmente
      en los próximos períodos) desde un mismo período de producción.
    """

    def __init__(
        self,
        problem,
        future_window: int = 4,
        setup_bias: float = 2.0,
        consolidation_weight: float = 1.0,
        holding_weight: float = 0.25,
        same_setup_bonus: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.future_window = future_window
        self.setup_bias = setup_bias
        self.consolidation_weight = consolidation_weight
        self.holding_weight = holding_weight
        self.same_setup_bonus = same_setup_bonus

    def score(self, partial, action) -> float:
        i = action.item
        t = action.period
        s = action.source
        qty = action.qty

        inst = self.inst
        rem_i = partial.rem[i]
        demand_now = rem_i[t] if t < len(rem_i) else 0.0

        # Demanda futura cercana del mismo ítem: si es alta, conviene consolidar
        # produciendo con setup activo o abriendo setup que cubra varios períodos.
        end = min(inst.n_periods, t + 1 + self.future_window)
        near_future = 0.0
        for tt in range(t + 1, end):
            near_future += rem_i[tt]

        # Más peso a lo que queda pendiente del ítem en el horizonte.
        total_remaining = 0.0
        for tt in range(t, inst.n_periods):
            total_remaining += rem_i[tt]

        setup_cost = inst.setup_cost[i]
        setup_time = inst.setup_time[i]
        holding_cost = inst.holding_cost[i]

        setup_active = bool(partial.setup[i][s])

        # Penaliza retrasar producción respecto al período que cubre.
        holding_penalty = max(0, t - s) * holding_cost

        # Si el setup ya está activo en source, esa acción consolida lotes
        # sin abrir un setup nuevo.
        if setup_active:
            setup_term = -self.same_setup_bonus
            # Si además cubre una fracción relevante de lo pendiente, mejor.
            consolidation_term = -self.consolidation_weight * (qty / (1.0 + total_remaining))
        else:
            # Abrir setup nuevo: penalización base, amortizada por la demanda futura
            # cercana que puede "absorberse" en el mismo período.
            future_amortization = near_future + 0.5 * total_remaining
            setup_term = self.setup_bias + setup_cost / (1.0 + future_amortization)
            # Si el setup es caro y hay poca demanda futura, la acción se vuelve peor.
            consolidation_term = self.consolidation_weight * (1.0 / (1.0 + qty + near_future))

        # Premia cubrir más de una demanda "útil" del mismo ítem con la misma acción.
        cover_term = -self.consolidation_weight * (qty / (1.0 + demand_now + near_future))

        # Pequeña preferencia por fuentes más tempranas cuando el setup ya existe
        # (aprovechar el setup activo antes de que se disperse la producción).
        source_term = 0.0
        if setup_active:
            source_term = 0.05 * max(0, t - s)

        score = (
            setup_term
            + holding_term * 0.0  # placeholder to keep structure explicit
            + consolidation_term
            + cover_term
            + self.holding_weight * holding_penalty
            + source_term
            + 0.001 * setup_time
        )

        # Garantía de finitud y estabilidad numérica.
        if score != score or score in (float("inf"), float("-inf")):
            return 1e18
        return float(score)


def build_component(
    problem,
    future_window: int = 4,
    setup_bias: float = 2.0,
    consolidation_weight: float = 1.0,
    holding_weight: float = 0.25,
    same_setup_bonus: float = 1.0,
):
    return SetupConsolidationUrgency(
        problem,
        future_window=future_window,
        setup_bias=setup_bias,
        consolidation_weight=consolidation_weight,
        holding_weight=holding_weight,
        same_setup_bonus=same_setup_bonus,
    )
