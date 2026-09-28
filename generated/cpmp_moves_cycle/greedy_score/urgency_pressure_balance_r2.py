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
        return len(stack)

    def _dest_future_pressure(self, dst, x):
        if not dst:
            return 0.0
        top = dst[-1]
        return 1.0 if top < x else 0.0

    def _stack_tension(self, stack):
        return sum(1.0 for i in range(len(stack) - 1) if stack[i] < stack[i + 1])

    def score(self, partial, action) -> float:
        stacks = partial.stacks
        so, sd = action
        src = stacks[so]
        dst = stacks[sd]
        x = src[-1]

        src_h = len(src)
        dst_h = len(dst)

        # Favor liberar fuentes más apiladas/menos ordenadas.
        source_penalty = 0.5 * src_h + self._stack_tension(src)

        # Prefer destinos más vacíos y donde el bloque quede sobre un tope no menor.
        pressure = self._dest_future_pressure(dst, x)
        dst_penalty = pressure + 0.15 * dst_h + 0.1 * self._stack_tension(dst)

        # Small tie-breaker to avoid overloading tall stacks.
        balance = dst_h / max(1, self.inst.H)

        return (
            -self.urgency_weight * source_penalty
            + self.pressure_weight * dst_penalty
            + self.balance_weight * balance
        )


def build_component(problem, urgency_weight: float = 2.0, pressure_weight: float = 1.5, balance_weight: float = 0.5):
    return UrgencyPressureBalance(problem, urgency_weight=urgency_weight, pressure_weight=pressure_weight, balance_weight=balance_weight)
