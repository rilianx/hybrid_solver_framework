COMPONENT = {
    "name": "two_high_single_blocker_safe_peel",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "source_height": {"type": "int", "range": [2, 6], "default": 2},
        "blocker_count": {"type": "int", "range": [1, 2], "default": 1},
    },
}

from core.rules import RuleMachine


class TwoHighSingleBlockerSafePeelRule:
    """Permite pelar el único bloqueador de una pila fuente muy baja y dejarlo en una pila destino ordenada sin desordenarla."""

    name = "two_high_single_blocker_safe_peel"

    def __init__(self, problem, source_height=2, blocker_count=1):
        self.problem = problem
        self.source_height = source_height
        self.blocker_count = blocker_count

    def _is_target_source(self, partial, so):
        h = partial.h(so)
        if h != self.source_height:
            return False
        if partial.is_sorted_stack(so):
            return False
        return h - partial.sorted_n[so] == self.blocker_count

    def _is_safe_sorted_destination(self, partial, so, sd):
        if so == sd:
            return False
        if not partial.is_sorted_stack(sd):
            return False
        if partial.e(sd) <= 0:
            return False
        moved = partial.g(so)
        return moved <= partial.g(sd)

    def allowed(self, partial, memory, candidates):
        selected = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if self._is_target_source(partial, so) and self._is_safe_sorted_destination(partial, so, sd):
                selected.append(action)

        selected.sort(
            key=lambda a: (
                partial.g(a.sd) - partial.g(a.so),
                -partial.sorted_n[a.sd],
                a.sd,
                a.so,
            )
        )
        return selected


def build_component(problem, **params):
    source_height = params.get("source_height", COMPONENT["params"]["source_height"]["default"])
    blocker_count = params.get("blocker_count", COMPONENT["params"]["blocker_count"]["default"])
    rule = TwoHighSingleBlockerSafePeelRule(
        problem,
        source_height=source_height,
        blocker_count=blocker_count,
    )
    return RuleMachine(problem, [rule])
