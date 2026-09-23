from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CLSPPartial

COMPONENT = {
    "name": "deadline_pressure",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "deadline_weight": {"type": "float", "range": [0.0, 10.0]},
        "scarcity_weight": {"type": "float", "range": [0.0, 10.0]},
        "future_hardness_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class DeadlinePressureScore:
    """Puntúa por urgencia: atiende primero lo más cercano al vencimiento y en períodos escasos.

    Menor es mejor. La idea es construir con sesgo a:
    - demandas de deadline más cercano;
    - períodos fuente con poca holgura relativa;
    - ítems cuyo futuro es más "duro" por su pendiente acumulada.
    """

    def __init__(
        self,
        problem,
        deadline_weight: float = 1.0,
        scarcity_weight: float = 1.0,
        future_hardness_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.deadline_weight = deadline_weight
        self.scarcity_weight = scarcity_weight
        self.future_hardness_weight = future_hardness_weight

    def score(self, partial: CLSPPartial, action) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source

        horizon = max(inst.n_periods - 1, 1)
        urgency = t / horizon

        free_s = partial.free(s)
        scarcity = 1.0 / (1.0 + max(free_s, 0.0))

        row_rem = partial.rem[i]
        future_demand = sum(row_rem[t:])
        past_demand = sum(row_rem[: t + 1])
        hardness = future_demand / max(past_demand + future_demand, 1e-12)

        source_earliness = (t - s) / max(inst.n_periods, 1)

        score = (
            self.deadline_weight * urgency
            + self.scarcity_weight * scarcity
            + self.future_hardness_weight * hardness
            + 0.1 * source_earliness
        )
        if not action.new_setup:
            score -= 0.05
        return score


def build_component(
    problem,
    deadline_weight: float = 1.0,
    scarcity_weight: float = 1.0,
    future_hardness_weight: float = 1.0,
):
    return DeadlinePressureScore(problem, deadline_weight, scarcity_weight, future_hardness_weight)
