COMPONENT = {
    "name": "safe_unlock_to_sorted_stack",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class SafeUnlockToSortedStack:
    name = "safe_unlock_to_sorted_stack"
    priority = 100

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        allowed = []
        for action in candidates:
            so, sd = action.so, action.sd
            if partial.sorted_n[so] >= len(partial.stacks[so]):
                continue

            c = partial.stacks[so][-1]
            if len(partial.stacks[sd]) >= partial.H:
                continue

            # Prefer moves that place a blocking container onto an already ordered stack
            # without breaking that stack's order.
            if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd):
                allowed.append(action)

        return allowed

    def score(self, partial, memory, action):
        so, sd = action.so, action.sd
        c = partial.stacks[so][-1]

        # Lower is better.
        # 1) Move from the most "unsettled" source first.
        # 2) Prefer compacting onto fuller sorted stacks.
        # 3) Prefer destinations with tighter tops when multiple choices remain.
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)

        return float(source_bad * 10_000 + dest_free * 100 + dest_top - c)


def build_component(problem, **params):
    return RuleMachine(problem, [SafeUnlockToSortedStack()])
