COMPONENT = {
    "name": "good_place_adaptive_transition_rule",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "stall_limit": {"type": "int", "range": [1, 12], "default": 3},
        "fallback_patience": {"type": "int", "range": [0, 8], "default": 1},
    },
}

from collections import namedtuple
from typing import Any

from core.rules import FALLBACK, RuleMachine


Move = namedtuple("Move", ["so", "sd"])


class GoodPlaceRule:
    name = "good_place"

    def __init__(self, problem):
        self.problem = problem

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        return memory

    def update(self, partial, memory, action):
        return memory

    def done(self, partial, memory):
        return True

    def propose(self, partial, memory):
        moves = []
        n_stacks = partial.S

        for so in range(n_stacks):
            if not partial.stacks[so]:
                continue

            c = partial.stacks[so][-1]

            for sd in range(n_stacks):
                if not partial.valid(so, sd):
                    continue

                dest_sorted = partial.is_sorted_stack(sd)
                dest_empty = len(partial.stacks[sd]) == 0
                can_be_well_placed = dest_empty or (c <= partial.g(sd))

                if not can_be_well_placed:
                    continue

                try:
                    cp = partial.copy(track=False)
                    cp.move(so, sd)
                    after_bad = cp.bad()
                    after_sorted = cp.sorted_n[sd]
                    after_ub = cp.ub(sd)
                except Exception:
                    after_bad = partial.bad()
                    after_sorted = partial.sorted_n[sd]
                    after_ub = partial.ub(sd)

                priority = (
                    0 if dest_sorted else 1,
                    0 if not dest_empty else 1,
                    after_bad,
                    -after_sorted,
                    after_ub,
                    so,
                    sd,
                )
                moves.append((priority, Move(so=so, sd=sd)))

        moves.sort(key=lambda x: x[0])
        return [m for _, m in moves]


class AdaptiveGoodPlaceTransitions:
    def __init__(self, rule_name: str, stall_limit: int = 3, fallback_patience: int = 1):
        self.rule_name = rule_name
        self.stall_limit = stall_limit
        self.fallback_patience = fallback_patience

    def initial(self, partial):
        return (partial.bad(), 0, 0)

    def select(self, partial, memory, rules):
        last_bad, stall_count, fallback_count = memory

        current_bad = partial.bad()
        if current_bad < last_bad:
            stall_count = 0
            fallback_count = 0
        elif current_bad == last_bad:
            stall_count += 1
        else:
            stall_count = 0

        if rules.applies(self.rule_name):
            if stall_count >= self.stall_limit and fallback_count < self.fallback_patience:
                return FALLBACK, (current_bad, stall_count, fallback_count + 1)
            return self.rule_name, (current_bad, stall_count, 0)

        return FALLBACK, (current_bad, stall_count, 0)


def build_component(problem, **params):
    stall_limit = params.get("stall_limit", COMPONENT["params"]["stall_limit"]["default"])
    fallback_patience = params.get("fallback_patience", COMPONENT["params"]["fallback_patience"]["default"])

    rule = GoodPlaceRule(problem)
    trans = AdaptiveGoodPlaceTransitions(
        rule.name,
        stall_limit=stall_limit,
        fallback_patience=fallback_patience,
    )
    return RuleMachine(problem, [rule], trans)
