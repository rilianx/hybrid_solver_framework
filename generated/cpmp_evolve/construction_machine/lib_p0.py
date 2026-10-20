COMPONENT = {
    "name": "origin_large_bad_top_gap",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "min_gap": {"type": "int", "range": [1, 100], "default": 6}
    },
}

from core.parts import origin_machine


class LargeBadTopGapOrigin:
    """Mueve desde pilas cuyo tope está claramente mal puesto sobre un grupo mucho menor."""

    name = "large_bad_top_gap"

    def __init__(self, min_gap: int):
        self.min_gap = int(min_gap)

    def init(self, partial):
        return None

    def update(self, partial, memory, action):
        return memory

    def _has_destination(self, partial, so):
        for sd in range(partial.S):
            if sd != so and partial.h(sd) < partial.H:
                return True
        return False

    def sources(self, partial, memory):
        candidates = []

        for so in range(partial.S):
            if partial.h(so) < 2:
                continue
            if not self._has_destination(partial, so):
                continue

            stack = partial.stacks[so]
            top = stack[-1]
            below = stack[-2]

            gap = top - below
            if gap < self.min_gap:
                continue

            candidates.append((gap, partial.h(so), so))

        candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
        return [so for _, _, so in candidates]


def build_component(problem, **params):
    min_gap = params.get("min_gap", COMPONENT["params"]["min_gap"]["default"])
    return origin_machine(problem, LargeBadTopGapOrigin(min_gap=min_gap))
