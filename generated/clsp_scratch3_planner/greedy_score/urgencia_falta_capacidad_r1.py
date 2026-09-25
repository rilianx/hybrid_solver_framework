from __future__ import annotations

import math
from typing import Any

from examples.lotsizing.problem_model import CoverAction, CLSPPartial

COMPONENT = {
    "name": "urgencia_falta_capacidad",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "urgency_weight": {"type": "float", "range": [0.0, 10.0]},
        "slack_weight": {"type": "float", "range": [0.0, 10.0]},
        "bottleneck_weight": {"type": "float", "range": [0.0, 20.0]},
        "setup_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class UrgenciaFaltaCapacidad:
    """Greedy score para CLSP: prioriza cubrir primero la demanda más urgente
    y gastar capacidad en períodos más apretados, castigando acciones que no
    alivian cuellos de botella.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        urgency_weight: float = 2.0,
        slack_weight: float = 2.0,
        bottleneck_weight: float = 6.0,
        setup_weight: float = 0.5,
    ):
        self.inst = problem.inst
        self.urgency_weight = float(urgency_weight)
        self.slack_weight = float(slack_weight)
        self.bottleneck_weight = float(bottleneck_weight)
        self.setup_weight = float(setup_weight)
        self._eps = 1e-9

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i, t, s = action.item, action.period, action.source

        pending = partial.rem[i][t]
        if pending <= 0.0:
            return float("inf")

        free_s = max(partial.free(s), 0.0)
        free_t = max(partial.free(t), 0.0)

        # Urgencia del ítem-período: cuanto más pendiente queda y más cerca
        # está del horizonte crítico, más interesa atenderlo.
        remaining_after_t = 0.0
        row = partial.rem[i]
        for k in range(t, inst.n_periods):
            remaining_after_t += row[k]
        urgency = pending / (1.0 + remaining_after_t)

        # Holgura remanente del período fuente: usar capacidad escasa para
        # quitar presión es valioso; usar capacidad holgada en un período poco
        # crítico es peor.
        scarcity_source = 1.0 / (1.0 + free_s)

        # Presión del deadline: más valioso si el período destino está apretado.
        deadline_pressure = 1.0 / (1.0 + free_t)

        # Acción que no "alivia" un cuello de botella: si el source tiene mucha
        # holgura, penalizamos; si hay que encender setup, también penalizamos
        # un poco salvo que la demanda sea muy urgente.
        bottleneck_relief = 1.0 / (1.0 + free_s) + 0.5 * (1.0 / (1.0 + free_t))
        setup_penalty = 1.0 if action.new_setup else 0.0

        # Preferimos cubrir más cantidad en la demanda crítica, pero sin
        # sobrepremiar lotes grandes cuando la urgencia es baja.
        qty_bonus = math.log1p(max(action.qty, 0.0))

        score = 0.0
        score -= self.urgency_weight * urgency
        score -= self.slack_weight * deadline_pressure
        score -= self.bottleneck_weight * bottleneck_relief * scarcity_source
        score += self.setup_weight * setup_penalty
        score -= 0.15 * qty_bonus

        # Pequeña preferencia por producir lo más cerca posible del deadline
        # cuando la urgencia es similar, pero sin convertirlo en criterio principal.
        dist = max(t - s, 0)
        score += 0.02 * dist

        if not math.isfinite(score):
            return float("inf")
        return float(score)


def build_component(problem, urgency_weight: float = 2.0, slack_weight: float = 2.0, bottleneck_weight: float = 6.0, setup_weight: float = 0.5):
    return UrgenciaFaltaCapacidad(
        problem,
        urgency_weight=urgency_weight,
        slack_weight=slack_weight,
        bottleneck_weight=bottleneck_weight,
        setup_weight=setup_weight,
    )
