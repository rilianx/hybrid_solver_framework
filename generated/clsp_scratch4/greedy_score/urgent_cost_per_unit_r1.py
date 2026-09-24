from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "urgent_cost_per_unit",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "setup_weight": {"type": "float", "range": [0.0, 10.0]},
        "holding_weight": {"type": "float", "range": [0.0, 10.0]},
        "lateness_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class UrgentCostPerUnit:
    """Puntúa cubrir demanda pendiente por su costo incremental inmediato.

    Idea:
    - favorece ítems con setup caro por unidad cubierta,
    - penaliza postergar al futuro por inventario,
    - penaliza usar un source muy temprano si la acción produce antes de la fecha,
      porque acumula inventario.

    Menor score = mejor.
    """

    def __init__(
        self,
        problem,
        setup_weight: float = 1.0,
        holding_weight: float = 1.0,
        lateness_weight: float = 0.5,
    ):
        self.inst: CLSPInstance = problem.inst
        self.setup_weight = float(setup_weight)
        self.holding_weight = float(holding_weight)
        self.lateness_weight = float(lateness_weight)

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source
        q = max(action.qty, 1e-12)

        setup_cost = inst.setup_cost[i] if action.new_setup else 0.0
        holding_cost = inst.holding_cost[i]

        # Costo por unidad: setup amortizado + inventario por producir antes del consumo.
        setup_term = self.setup_weight * (setup_cost / q)
        hold_term = self.holding_weight * holding_cost * max(0, t - s)
        lateness_term = self.lateness_weight * (t - s) / max(1, t + 1)

        # Ligera preferencia por usar capacidad más tardía cuando el período objetivo es lejano
        # (evita llenar demasiado pronto si no hace falta).
        free_term = 0.001 * (1.0 / (1.0 + max(partial.free(s), 0.0)))

        return setup_term + hold_term + lateness_term + free_term


def build_component(problem, setup_weight: float = 1.0, holding_weight: float = 1.0, lateness_weight: float = 0.5):
    return UrgentCostPerUnit(problem, setup_weight=setup_weight, holding_weight=holding_weight, lateness_weight=lateness_weight)
