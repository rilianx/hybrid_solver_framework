from __future__ import annotations

from dataclasses import dataclass

COMPONENT = {
    "name": "blocking_reduction_with_safe_landing",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "block_weight": {"type": "float", "range": [0.0, 10.0]},
        "landing_weight": {"type": "float", "range": [0.0, 10.0]},
        "source_penalty": {"type": "float", "range": [0.0, 10.0]},
    },
}


@dataclass
class BlockingReductionWithSafeLanding:
    """CPMP: puntúa mover el tope de una pila. Prefiere acciones que
    desbloquean más contenedores en la pila origen y que aterrizan en una
    pila compatible (tope mayor o pila vacía), evitando dejar el tope nuevo
    de la pila destino mal ordenado. Menor puntaje = mejor."""

    def __init__(self, problem, block_weight: float = 2.0, landing_weight: float = 1.0, source_penalty: float = 0.5):
        self.inst = problem.inst
        self.block_weight = float(block_weight)
        self.landing_weight = float(landing_weight)
        self.source_penalty = float(source_penalty)

    def _as_stacks(self, partial):
        return partial.stacks

    def _blocking_above(self, stack, idx):
        x = stack[idx]
        return sum(1 for j in range(idx + 1, len(stack)) if stack[j] > x)

    def _source_disorder_loss(self, stack):
        # How much disorder is removed if the top is taken away.
        if len(stack) < 2:
            return 0
        before = sum(1 for i in range(len(stack) - 1) if stack[i] < stack[i + 1])
        after = sum(1 for i in range(len(stack) - 2) if stack[i] < stack[i + 1])
        return before - after

    def score(self, partial, action) -> float:
        stacks = self._as_stacks(partial)
        so, sd = action
        src = stacks[so]
        dst = stacks[sd]
        x = src[-1]

        blocking = self._blocking_above(src, len(src) - 1)
        source_gain = self._source_disorder_loss(src)

        # Safe landing if destination is empty or already has a top >= moved item.
        safe = 1.0 if (not dst or dst[-1] >= x) else 0.0

        # Prefer destinations that do not create a new increasing pair on top.
        dest_penalty = 0.0
        if dst:
            dest_penalty = 1.0 if dst[-1] < x else 0.0

        # Mild preference for using less crowded destination stacks.
        load = len(dst) / max(1, self.inst.H)

        return (
            self.block_weight * float(blocking)
            - self.source_penalty * float(source_gain)
            + self.landing_weight * (1.0 - safe + dest_penalty + load)
        )


def build_component(problem, block_weight: float = 2.0, landing_weight: float = 1.0, source_penalty: float = 0.5):
    return BlockingReductionWithSafeLanding(problem, block_weight=block_weight, landing_weight=landing_weight, source_penalty=source_penalty)
