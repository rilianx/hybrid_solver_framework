from __future__ import annotations

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
    """CLSP greedy score: favorece consolidar demanda de un mismo ítem en menos períodos.

    Menor score = mejor.
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
        n_periods = inst.n_periods

        demand_now = rem_i[t] if 0 <= t < len(rem_i) else 0.0

        end = min(n_periods, t + 1 + self.future_window)
        near_future = 0.0
        for tt in range(t + 1, end):
            near_future += rem_i[tt]

        total_remaining = 0.0
        for tt in range(t, n_periods):
            total_remaining += rem_i[tt]

        setup_cost = inst.setup_cost[i]
        setup_time = inst.setup_time[i]
        holding_cost = inst.holding_cost[i]

        setup_active = bool(partial.setup[i][s])

        # Penaliza producir "tarde" respecto al source; cuanto más se aleja,
        # más inventario implícito puede haber que sostener.
        holding_penalty = max(0, t - s) * holding_cost

        if setup_active:
            # Ya existe setup activo para este ítem en el source: consolidación deseable.
            setup_term = -self.same_setup_bonus
            consolidation_term = -self.consolidation_weight * (qty / (1.0 + total_remaining))
        else:
            # Abrir setup nuevo: penalización base, más alta si la demanda futura cercana
            # es pequeña y no amortiza el cambio.
            future_amortization = near_future + 0.5 * total_remaining
            setup_term = self.setup_bias + setup_cost / (1.0 + future_amortization)
            consolidation_term = self.consolidation_weight * (1.0 / (1.0 + qty + near_future))

        # Favorece cubrir demanda relevante del ítem con esta acción.
        cover_term = -self.consolidation_weight * (qty / (1.0 + demand_now + near_future))

        # Pequeña preferencia por usar setups activos en fuentes más tempranas.
        source_term = 0.0
        if setup_active:
            source_term = 0.05 * max(0, t - s)

        score = (
            setup_term
            + consolidation_term
            + cover_term
            + self.holding_weight * holding_penalty
            + source_term
            + 0.001 * setup_time
        )

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
