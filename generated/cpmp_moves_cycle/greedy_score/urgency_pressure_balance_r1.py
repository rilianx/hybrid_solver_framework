from __future__ import annotations

from dataclasses import dataclass

COMPONENT = {
    "name": "urgency_pressure_balance",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "urgency_weight": {"type": "float", "range": [0.0, 10.0]},
        "pressure_weight": {"type": "float", "range": [0.0, 10.0]},
        "balance_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


@dataclass
class UrgencyPressureBalance:
    """CPMP: puntúa mover el tope según cuán urgente es liberar esa pila y
    cuánta presión futura introduce en la pila destino. El criterio favorece
    extraer contenedores 'difíciles' de pilas muy bloqueadas y enviar las piezas
    a destinos con más holgura. Menor puntaje = mejor."""

    def __init__(self, problem, urgency_weight: float = 2.0, pressure_weight: float = 1.5, balance_weight: float = 0.5):
        self.inst = problem.inst
        self.urgency_weight = float(urgency_weight)
        self.pressure_weight = float(pressure_weight)
        self.balance_weight = float(balance_weight)

    def _blocking_depth(self, stack):
        # Number of containers above the top? Here top is last, so depth proxy is stack height.
        return len(stack)

    def _dest_future_pressure(self, dst, x):
        if not dst:
            return 0.0
        top = dst[-1]
        # If x is larger than the destination top, it will create an increasing pair.
        return 1.0 if top < x else 0.0

    def _stack_tension(self, stack):
        # Count local increasing adjacencies in the whole stack.
        return sum(1.0 for i in range(len(stack) - 1) if stack[i] < stack[i + 1])

    def score(self, partial, action) -> float:
        stacks = partial.stacks
        so, sd = action
        src = stacks[so]
        dst = stacks[sd]
        x = src[-1]

        # More urgent if source stack is taller and currently more disordered.
        urgency = float(self._stack_tension(src) + 0.25 * self._blocking_depth(src))

        # Pressure created in the destination if the move places a larger block on top of a smaller one.
        pressure = self._dest_future_pressure(dst, x) + 0.1 * self._stack_tension(dst)

        # Encourage moving toward less loaded stacks to preserve maneuverability.
        balance = len(dst) / max(1, self.inst.H)

        return (
            -self.urgency_weight * urgency
            + self.pressure_weight * pressure
            + self.balance_weight * balance
        )


def build_component(problem, urgency_weight: float = 2.0, pressure_weight: float = 1.5, balance_weight: float = 0.5):
    return UrgencyPressureBalance(problem, urgency_weight=urgency_weight, pressure_weight=pressure_weight, balance_weight=balance_weight)
