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

    def __init__(self, problem, block_weight: float = 1.0, landing_weight: float = 2.0, source_penalty: float = 0.25):
        self.problem = problem
        self.block_weight = float(block_weight)
        self.landing_weight = float(landing_weight)
        self.source_penalty = float(source_penalty)

    def _as_stacks(self, partial):
        return partial.stacks

    def _blocking_above(self, stack, idx):
        x = stack[idx]
        return sum(1 for j in range(idx + 1, len(stack)) if stack[j] > x)

    def _source_disorder_loss(self, stack):
        # Prefer removing a top container that is "too large" for many containers
        # below it, since this often exposes a better future top.
        if len(stack) < 2:
            return 0
        x = stack[-1]
        return sum(1 for v in stack[:-1] if v < x)

    def score(self, partial, action) -> float:
        stacks = partial.stacks
        so, sd = action
        src = stacks[so]
        dst = stacks[sd]
        x = src[-1]
        inst = self.problem.inst

        # Source benefit: removing a container that dominates many below it is useful.
        source_gain = sum(1 for v in src[:-1] if v < x)

        # Destination quality: penalize unsafe landings strongly.
        if not dst:
            landing_penalty = 0.0
        else:
            top = dst[-1]
            landing_penalty = 0.0 if top >= x else 2.0 + (x - top) / max(1, inst.H)

        # Mild preference for landing on shorter stacks.
        load_penalty = len(dst) / max(1, inst.H)

        # Slight preference for taking from taller stacks.
        source_load = len(src) / max(1, inst.H)

        return (
            self.landing_weight * (landing_penalty + load_penalty)
            + self.block_weight * source_load
            - self.source_penalty * float(source_gain)
        )


def build_component(problem, block_weight: float = 1.0, landing_weight: float = 2.0, source_penalty: float = 0.25):
    return BlockingReductionWithSafeLanding(problem, block_weight=block_weight, landing_weight=landing_weight, source_penalty=source_penalty)
