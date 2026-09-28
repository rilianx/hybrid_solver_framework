from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COMPONENT = {
    "name": "reserve_buffer_then_repair_policy",
    "slot": "construction_policy",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "buffer_weight": {"type": "float", "range": [0.2, 5.0]},
        "repair_weight": {"type": "float", "range": [0.2, 5.0]},
        "switch_patience": {"type": "int", "range": [1, 6]},
    },
}


@dataclass(frozen=True)
class _Memory:
    phase: str  # "buffer" or "repair"
    buffer_stack: int
    patience: int
    last_source: int


class ReserveBufferThenRepairPolicy:
    """Política en dos fases:
    1) reservar una pila tampón con espacio libre y usarla como destino preferente;
    2) cuando el layout queda suficientemente 'abierto', pasar a reparar con movimientos más directos.

    La memoria fija una pila tampón, distinta de las políticas anteriores, y alterna entre una fase
    de acumulación y una de reparación.
    """

    def __init__(self, problem, buffer_weight: float = 1.2, repair_weight: float = 1.0, switch_patience: int = 2):
        self.problem = problem
        self.inst = problem.inst
        self.buffer_weight = float(buffer_weight)
        self.repair_weight = float(repair_weight)
        self.switch_patience = int(switch_patience)

    def _ordered(self, stack: tuple[int, ...]) -> bool:
        return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))

    def _disorder(self, stacks: tuple[tuple[int, ...], ...]) -> int:
        return sum(1 for s in stacks for i in range(len(s) - 1) if s[i] < s[i + 1])

    def _pick_buffer(self, partial) -> int:
        best = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            free = self.inst.H - len(s)
            ordered_bonus = 0 if self._ordered(s) else 1
            key = (-free, ordered_bonus, len(s), i)
            if best is None or key < best_key:
                best = i
                best_key = key
        return int(best if best is not None else 0)

    def init(self, partial: Any) -> _Memory:
        return _Memory(phase="buffer", buffer_stack=self._pick_buffer(partial), patience=0, last_source=-1)

    def score(self, partial: Any, memory: _Memory, action: Any) -> float:
        so, sd = int(action[0]), int(action[1])
        x = partial.stacks[so][-1]
        dst_top = partial.stacks[sd][-1] if partial.stacks[sd] else None
        score = 0.0

        if memory.phase == "buffer":
            # Build a robust buffer stack with free space.
            if sd == memory.buffer_stack:
                score -= self.buffer_weight
            if so == memory.buffer_stack:
                score += 0.2
        else:
            # Repair phase: prefer moves that directly improve local order.
            if so == memory.last_source:
                score -= self.repair_weight
            if sd == memory.buffer_stack:
                score += 0.3

        if dst_top is None or dst_top >= x:
            score -= 0.2
        else:
            score += 1.0

        # Prefer moving from disordered stacks.
        if not self._ordered(partial.stacks[so]):
            score -= 0.15
        else:
            score += 0.15

        # Mild preference for smaller destination stacks to keep room available.
        score += 0.01 * len(partial.stacks[sd])

        return float(score)

    def update(self, partial: Any, memory: _Memory, action: Any) -> _Memory:
        so, sd = int(action[0]), int(action[1])

        if memory.phase == "buffer":
            # Switch once the buffer is not the obvious sink anymore or patience is spent.
            if sd == memory.buffer_stack:
                return _Memory(phase="buffer", buffer_stack=memory.buffer_stack, patience=0, last_source=so)

            patience = min(memory.patience + 1, self.switch_patience)
            if patience >= self.switch_patience:
                return _Memory(phase="repair", buffer_stack=memory.buffer_stack, patience=0, last_source=so)
            return _Memory(phase="buffer", buffer_stack=memory.buffer_stack, patience=patience, last_source=so)

        # Repair phase: keep the same buffer, but reset when we use a different source.
        if so != memory.last_source:
            return _Memory(phase="repair", buffer_stack=memory.buffer_stack, patience=0, last_source=so)
        return _Memory(phase="repair", buffer_stack=memory.buffer_stack, patience=memory.patience, last_source=memory.last_source)


def build_component(problem, buffer_weight: float = 1.2, repair_weight: float = 1.0, switch_patience: int = 2):
    return ReserveBufferThenRepairPolicy(
        problem,
        buffer_weight=buffer_weight,
        repair_weight=repair_weight,
        switch_patience=switch_patience,
    )
