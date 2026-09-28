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

        # Source "badness": prefer moving from stacks that are already disordered.
        src_bad = 0.0
        for i in range(len(src) - 1):
            if src[i] < src[i + 1]:
                src_bad += 1.0

        # Destination preference: empty stacks are best refuges; otherwise prefer
        # placing on a top container that is not smaller than x.
        if not dst:
            dst_bad = 0.0
        elif dst[-1] >= x:
            dst_bad = 0.5
        else:
            dst_bad = 6.0 + (x - dst[-1]) * 0.1

        # Mild preference for freeing space from taller stacks, but keep it small
        # so the score is still dominated by immediate feasibility quality.
        height_bias = 0.05 * len(src)

        # Mild preference for using destinations with more remaining capacity.
        cap_bias = 0.02 * len(dst)

        return (
            self.preserve_weight * src_bad
            + self.refuge_weight * dst_bad
            + self.compactness_weight * cap_bias
            + height_bias
        )


def build_component(problem, preserve_weight: float = 3.0, refuge_weight: float = 2.0, compactness_weight: float = 0.5):
    return OrderPreservationRefugeChoice(problem, preserve_weight=preserve_weight, refuge_weight=refuge_weight, compactness_weight=compactness_weight)
