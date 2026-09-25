from __future__ import annotations

from examples.lotsizing.problem_model import CLSPInstance, CoverAction, CLSPPartial


COMPONENT = {
    "name": "setup_amortization_by_quantity",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "setup_weight": {"type": "float", "range": [0.0, 10.0]},
        "holding_weight": {"type": "float", "range": [0.0, 5.0]},
        "quantity_weight": {"type": "float", "range": [0.0, 5.0]},
        "reuse_bonus_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class SetupAmortizationByQuantity:
    """Prefiere acciones que amortizan setups caros con mucha cantidad.

    Menor puntaje = mejor. La idea es:
    - evitar pagar setups caros para cubrir poca cantidad;
    - si ya existe setup en la fuente, favorecer su reutilización;
    - penalizar inventario, pero menos que el coste de setup amortizado.
    """

    def __init__(
        self,
        problem,
        setup_weight: float = 1.0,
        holding_weight: float = 0.5,
        quantity_weight: float = 1.0,
        reuse_bonus_weight: float = 1.0,
    ):
        self.inst: CLSPInstance = problem.inst
        self.setup_weight = setup_weight
        self.holding_weight = holding_weight
        self.quantity_weight = quantity_weight
        self.reuse_bonus_weight = reuse_bonus_weight

    def score(self, partial: CLSPPartial, action: CoverAction) -> float:
        inst = self.inst
        i = action.item
        t = action.period
        s = action.source
        q = max(float(action.qty), 1e-9)

        # Setup amortizado por unidad cubierta: si hay nuevo setup, penaliza más cuando q es pequeño.
        setup_cost = inst.setup_cost[i] if action.new_setup else 0.0
        amortized_setup = self.setup_weight * (setup_cost / q)

        # Inventario esperado por adelantar producción desde s a t.
        holding = self.holding_weight * inst.holding_cost[i] * float(t - s)

        # Preferir cubrir más unidades por acción.
        quantity_term = -self.quantity_weight * q

        # Si la fuente ya está abierta para ese ítem, mejor.
        reuse_bonus = -self.reuse_bonus_weight * (1.0 if partial.setup[i][s] else 0.0)

        return amortized_setup + holding + quantity_term + reuse_bonus


def build_component(problem, setup_weight: float = 1.0, holding_weight: float = 0.5,
                    quantity_weight: float = 1.0, reuse_bonus_weight: float = 1.0):
    return SetupAmortizationByQuantity(
        problem,
        setup_weight=setup_weight,
        holding_weight=holding_weight,
        quantity_weight=quantity_weight,
        reuse_bonus_weight=reuse_bonus_weight,
    )
