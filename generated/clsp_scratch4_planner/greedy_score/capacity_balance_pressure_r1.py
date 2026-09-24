from __future__ import annotations

from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "capacity_balance_pressure",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "target_pressure_weight": {"type": "float", "range": [0.0, 5.0]},
        "new_setup_penalty": {"type": "float", "range": [0.0, 2.0]},
    },
}


class CapacityBalancePressure:
    """Criterio greedy para CLSP.

    Favorece acciones que:
    - consumen capacidad en períodos de origen con más holgura relativa,
    - y cubren demandas cuyo período objetivo está más congestionado.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        target_pressure_weight: float = 1.5,
        new_setup_penalty: float = 0.1,
    ) -> None:
        self.inst: CLSPInstance = problem.inst
        self.target_pressure_weight = target_pressure_weight
        self.new_setup_penalty = new_setup_penalty

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        t = action.period
        s = action.source
        i = action.item
        qty = action.qty

        cap_t = inst.capacity[t]
        cap_s = inst.capacity[s]

        # Presión del período objetivo: cuánto demandada pendiente sigue concentrada allí.
        pending_t = 0.0
        row_t = partial.rem
        for k in range(inst.n_items):
            pending_t += row_t[k][t]

        target_pressure = pending_t / max(cap_t, 1e-9)

        # Holgura relativa del período de origen tras ejecutar la acción.
        added_setup = inst.setup_time[i] if action.new_setup else 0.0
        source_util_after = (partial.used[s] + qty + added_setup) / max(cap_s, 1e-9)

        # Pequeño sesgo para no abrir setups nuevos si hay alternativas equivalentes.
        setup_term = self.new_setup_penalty if action.new_setup else 0.0

        return source_util_after - self.target_pressure_weight * target_pressure + setup_term


def build_component(problem, target_pressure_weight: float = 1.5, new_setup_penalty: float = 0.1):
    return CapacityBalancePressure(
        problem,
        target_pressure_weight=target_pressure_weight,
        new_setup_penalty=new_setup_penalty,
    )
