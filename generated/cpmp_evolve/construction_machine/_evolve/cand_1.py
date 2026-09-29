COMPONENT = {
    "name": "safe_placement",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class SafePlacementRule:
    name = "safe_placement"
    priority = 100

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        def key(action):
            c = partial.g(action.so)
            dest_empty = partial.h(action.sd) == 0
            compatible = dest_empty or partial.g(action.sd) >= c
            # Prefer moves that place the block on a compatible stack,
            # especially on an already sorted destination stack.
            return (
                0 if compatible else 1,
                0 if partial.is_sorted_stack(action.sd) else 1,
                0 if not partial.is_sorted_stack(action.so) else 1,
                partial.h(action.sd),
                action.so,
                action.sd,
            )

        chosen = [a for a in candidates if partial.h(a.sd) == 0 or partial.g(a.sd) >= partial.g(a.so)]
        return sorted(chosen, key=key)


def build_component(problem, **params):
    return RuleMachine(problem, [SafePlacementRule()])
