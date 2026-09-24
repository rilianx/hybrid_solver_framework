from __future__ import annotations

from typing import Protocol

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "setup_and_holding_tradeoff",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "holding_weight": {"type": "float", "range": [0.0, 10.0]},
        "setup_weight": {"type": "float", "range": [0.0, 10.0]},
        "early_use_bonus": {"type": "float", "range": [0.0, 5.0]},
    },
}


class SetupAndHoldingTradeoff:
    """Puntúa cubrir demanda con un balance entre costo de setup, inventario esperado y
    preferencia por usar períodos tempranos cuando no encarece demasiado.

    Idea:
    - si hay que abrir un setup nuevo, penaliza su costo fijo;
    - penaliza producir muy antes del deadline usando una aproximación simple de inventario;
    - favorece fuentes tempranas porque suelen dejar más flexibilidad al resto.
    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        holding_weight: float = 1.0,
        setup_weight: float = 1.0,
        early_use_bonus: float = 0.15,
    ):
        self.inst: CLSPInstance = problem.inst
        self.holding_weight = holding_weight
        self.setup_weight = setup_weight
        self.early_use_bonus = early_use_bonus

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i, t, s, q = action.item, action.period, action.source, action.qty

        # Aproximación de inventario: cada unidad producida en s para cubrir t paga (t-s) períodos de holding.
        inventory_cost = inst.holding_cost[i] * max(0, t - s) * q

        # Penalización por encender un nuevo setup.
        setup_cost = inst.setup_cost[i] if action.new_setup else 0.0

        # Incentivo suave por usar antes períodos tempranos.
        early_bonus = self.early_use_bonus * s * q

        # Ligera preferencia por consumos que dejan más holgura, pero sin mirar factibilidad futura.
        slack_after = partial.free(s) - (inst.setup_time[i] if action.new_setup else 0.0) - q
        slack_penalty = 0.0 if slack_after >= 0 else 1e6

        return (
            self.setup_weight * setup_cost
            + self.holding_weight * inventory_cost
            + slack_penalty
            + early_bonus
        )


def build_component(problem, holding_weight: float = 1.0, setup_weight: float = 1.0, early_use_bonus: float = 0.15):
    return SetupAndHoldingTradeoff(
        problem,
        holding_weight=holding_weight,
        setup_weight=setup_weight,
        early_use_bonus=early_use_bonus,
    )
