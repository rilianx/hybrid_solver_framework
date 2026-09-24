from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction


COMPONENT = {
    "name": "coste_holding_setup_inmediato",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "setup_amortization_weight": {"type": "float", "range": [0.0, 10.0]},
        "holding_weight": {"type": "float", "range": [0.0, 10.0]},
        "gap_bias": {"type": "float", "range": [0.0, 5.0]},
        "epsilon": {"type": "float", "range": [1e-12, 1e-3]},
    },
}


class CosteHoldingSetupInmediato:
    """Puntúa una acción por el coste incremental local de cubrirla ahora desde `source`.

    Idea:
    - amortiza el coste de setup sobre la cantidad cubierta cuando hace falta abrir un nuevo lote;
    - añade el holding esperado por producir antes del deadline;
    - normaliza por la cantidad cubierta para comparar acciones de distinto tamaño.

    Menor puntaje = mejor.
    """

    def __init__(
        self,
        problem,
        setup_amortization_weight: float = 1.0,
        holding_weight: float = 1.0,
        gap_bias: float = 0.0,
        epsilon: float = 1e-9,
    ):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.setup_amortization_weight = setup_amortization_weight
        self.holding_weight = holding_weight
        self.gap_bias = gap_bias
        self.epsilon = epsilon

    def score(self, partial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        source = action.source
        period = action.period
        qty = action.qty

        q = qty if qty > self.epsilon else self.epsilon
        gap = period - source
        if gap < 0:
            gap = 0

        setup_cost = inst.setup_cost[i] if action.new_setup else 0.0
        holding_cost = inst.holding_cost[i]

        # Coste aproximado por unidad:
        # - setup amortizado si hay que encender el ítem en `source`
        # - holding lineal por cada período que la unidad permanece inventariada
        # - pequeño sesgo para preferir, a igualdad de coste, producir más cerca del deadline
        per_unit = (
            self.setup_amortization_weight * (setup_cost / q)
            + self.holding_weight * (holding_cost * gap)
            + self.gap_bias * gap
        )

        return per_unit


def build_component(problem, setup_amortization_weight: float = 1.0, holding_weight: float = 1.0, gap_bias: float = 0.0, epsilon: float = 1e-9):
    return CosteHoldingSetupInmediato(
        problem,
        setup_amortization_weight=setup_amortization_weight,
        holding_weight=holding_weight,
        gap_bias=gap_bias,
        epsilon=epsilon,
    )
