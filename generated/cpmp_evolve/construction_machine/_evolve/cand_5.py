COMPONENT = {
    "name": "good_place_tight_fit_rule",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
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
        big = n_stacks + partial.H + 1

        for so in range(n_stacks):
            if not partial.stacks[so]:
                continue

            c = partial.stacks[so][-1]
            source_ub = partial.ub(so)

            for sd in range(n_stacks):
                if not partial.valid(so, sd):
                    continue

                dest_empty = len(partial.stacks[sd]) == 0
                can_be_well_placed = dest_empty or (c <= partial.g(sd))
                if not can_be_well_placed:
                    continue

                try:
                    cp = partial.copy(track=False)
                    cp.move(so, sd)
                    after_bad = cp.bad()
                    after_total_ub = sum(cp.ub(i) for i in range(cp.S))
                    after_sorted = cp.sorted_n[sd]
                except Exception:
                    after_bad = partial.bad()
                    after_total_ub = sum(partial.ub(i) for i in range(partial.S))
                    after_sorted = partial.sorted_n[sd]

                dest_top = partial.g(sd) if not dest_empty else big

                # Prefer:
                # 1) destinations already sorted,
                # 2) non-empty destinations before empty ones,
                # 3) lower remaining bad blocks,
                # 4) lower remaining unlocked bad blocks,
                # 5) tighter fits (smaller destination top),
                # 6) sources with more unlocked bad blocks,
                # 7) deterministic tie-breaks.
                priority = (
                    0 if partial.is_sorted_stack(sd) else 1,
                    0 if not dest_empty else 1,
                    after_bad,
                    after_total_ub,
                    dest_top,
                    -source_ub,
                    -after_sorted,
                    so,
                    sd,
                )
                moves.append((priority, Move(so=so, sd=sd)))

        moves.sort(key=lambda x: x[0])
        return [m for _, m in moves]


class GreedyGoodPlaceTransitions:
    def __init__(self, rule_name: str):
        self.rule_name = rule_name

    def initial(self, partial):
        return ()

    def select(self, partial, memory, rules):
        if rules.applies(self.rule_name):
            return self.rule_name, memory
        return FALLBACK, memory


def build_component(problem, **params):
    rule = GoodPlaceRule(problem)
    trans = GreedyGoodPlaceTransitions(rule.name)
    return RuleMachine(problem, [rule], trans)
