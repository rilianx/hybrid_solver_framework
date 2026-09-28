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

        preserve = self._source_order_risk(src)
        refuge = 1.0 - self._is_refuge(dst, x)

        # Prefer destinations with more remaining capacity, as they are more useful later.
        compactness = 1.0 - (self.inst.H - len(dst)) / max(1, self.inst.H)

        # Slightly reward moving from fuller stacks, since that opens maneuvering space.
        source_fullness = len(src) / max(1, self.inst.H)

        return (
            self.preserve_weight * preserve
            + self.refuge_weight * refuge
            + self.compactness_weight * compactness
            - 0.1 * source_fullness
        )


def build_component(problem, preserve_weight: float = 3.0, refuge_weight: float = 2.0, compactness_weight: float = 0.5):
    return OrderPreservationRefugeChoice(problem, preserve_weight=preserve_weight, refuge_weight=refuge_weight, compactness_weight=compactness_weight)
