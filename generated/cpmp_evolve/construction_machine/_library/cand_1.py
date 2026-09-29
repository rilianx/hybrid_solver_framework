COMPONENT = {
    "name": "single_blocker_peel",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "min_source_height": {"type": "int", "range": [1, 10], "default": 2},
        "bad_containers_in_source": {"type": "int", "range": [1, 3], "default": 1},
        "require_sorted_destination": {"type": "bool", "default": True},
        "prefer_tighter_destination": {"type": "bool", "default": True},
    },
}

from core.rules import RuleMachine


class SingleBlockerPeelRule:
    """Permite sacar el único bloqueador del tope de una pila casi ordenada."""

    name = "single_blocker_peel"

    def __init__(
        self,
        min_source_height=2,
        bad_containers_in_source=1,
        require_sorted_destination=True,
        prefer_tighter_destination=True,
    ):
        self.min_source_height = min_source_height
        self.bad_containers_in_source = bad_containers_in_source
        self.require_sorted_destination = require_sorted_destination
        self.prefer_tighter_destination = prefer_tighter_destination

    def _is_peel_source(self, partial, so):
        height = partial.h(so)
        if height < self.min_source_height:
            return False
        good_from_bottom = partial.sorted_n[so]
        bad_in_source = height - good_from_bottom
        if bad_in_source != self.bad_containers_in_source:
            return False
        return good_from_bottom == height - self.bad_containers_in_source

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._is_peel_source(partial, so):
                continue
            if self.require_sorted_destination and not partial.is_sorted_stack(sd):
                continue
            allowed.append(action)

        if not self.prefer_tighter_destination:
            return allowed

        return sorted(
            allowed,
            key=lambda a: (
                partial.e(a.sd),
                -partial.h(a.sd),
                partial.g(a.sd),
                a.sd,
                a.so,
            ),
        )


def build_component(
    problem,
    min_source_height=2,
    bad_containers_in_source=1,
    require_sorted_destination=True,
    prefer_tighter_destination=True,
):
    rule = SingleBlockerPeelRule(
        min_source_height=min_source_height,
        bad_containers_in_source=bad_containers_in_source,
        require_sorted_destination=require_sorted_destination,
        prefer_tighter_destination=prefer_tighter_destination,
    )
    return RuleMachine(problem, [rule])
