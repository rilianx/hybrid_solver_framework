from __future__ import annotations

from dataclasses import dataclass

COMPONENT = {
    "name": "order_preservation_refuge_choice",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "preserve_weight": {"type": "float", "range": [0.0, 10.0]},
        "refuge_weight": {"type": "float", "range": [0.0, 10.0]},
        "compactness_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


@dataclass
class OrderPreservationRefugeChoice:
    """CPMP: puntúa acciones que preservan pilas ya ordenadas y prefieren
    destinos-refugio: pilas vacías o con tope suficientemente grande.
    También favorece mantener compactación dejando espacio en pilas más llenas
    para movimientos futuros. Menor puntaje = mejor."""

    def __init__(self, problem, preserve_weight: float = 3.0, refuge_weight: float = 2.0, compactness_weight: float = 0.5):
        self.inst = problem.inst
        self.preserve_weight = float(preserve_weight)
        self.refuge_weight = float(refuge_weight)
        self.compactness_weight = float(compactness_weight)

    def _ordered(self, stack) -> bool:
        return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))

    def _is_refuge(self, dst, x) -> float:
        return 1.0 if (not dst or dst[-1] >= x) else 0.0

    def _source_order_risk(self, src) -> float:
        # Removing the top from an ordered stack is "safer" than from a disordered one.
        if self._ordered(src):
            return 0.0
        return sum(1.0 for i in range(len(src) - 1) if src[i] < src[i + 1])

    def score(self, partial, action) -> float:
        stacks = partial.stacks
        so, sd = action
        src = stacks[so]
        dst = stacks[sd]
        x = src[-1]

        # Source quality: prioritize moving from stacks that already contain disorder.
        src_bad = 0.0
        for i in range(len(src) - 1):
            if src[i] < src[i + 1]:
                src_bad += 1.0

        # Destination quality:
        # - empty stacks are the best refuge,
        # - otherwise prefer destinations whose top can support x,
        # - otherwise penalize strongly increasing the stack disorder.
        if not dst:
            dst_bad = 0.0
        else:
            top = dst[-1]
            if top >= x:
                # Prefer tighter refuges that keep the stack ordered but not too tall.
                dst_bad = 0.15 + 0.03 * max(0, len(dst) - 1)
            else:
                # Strong penalty for creating an inverted pair, scaled by gap.
                dst_bad = 8.0 + 0.2 * (x - top)

        # Compactness: slightly prefer using shorter destinations so that larger
        # stacks remain available as future shelters.
        dst_height_bias = 0.03 * len(dst)

        # Avoid depleting very short sources unless they are already disordered.
        src_height_bias = 0.01 * len(src)

        return (
            self.preserve_weight * src_bad
            + self.refuge_weight * dst_bad
            + self.compactness_weight * dst_height_bias
            + src_height_bias
        )


def build_component(problem, preserve_weight: float = 3.0, refuge_weight: float = 2.0, compactness_weight: float = 0.5):
    return OrderPreservationRefugeChoice(problem, preserve_weight=preserve_weight, refuge_weight=refuge_weight, compactness_weight=compactness_weight)
