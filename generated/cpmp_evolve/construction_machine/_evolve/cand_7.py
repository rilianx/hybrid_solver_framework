COMPONENT = {
    "name": "good_place_refined_rank_rule",
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
        base_bad = partial.bad()

        for so in range(n_stacks):
            if not partial.stacks[so]:
                continue

            c = partial.stacks[so][-1]

            for sd in range(n_stacks):
                if not partial.valid(so, sd):
                    continue

                dest_sorted = partial.is_sorted_stack(sd)
                dest_empty = len(partial.stacks[sd]) == 0
                compatible_dest = dest_empty or (dest_sorted and c <= partial.g(sd))

                try:
                    cp = partial.copy(track=False)
                    cp.move(so, sd)
                    after_bad = cp.bad()
                    after_sorted_total = sum(cp.sorted_n)
                    after_sorted_sd = cp.sorted_n[sd]
                    after_sorted_so = cp.sorted_n[so]
                    after_ub_sd = cp.ub(sd)
                    after_ub_so = cp.ub(so)
                    after_ub_total = after_ub_sd + after_ub_so
                except Exception:
                    after_bad = base_bad
                    after_sorted_total = sum(partial.sorted_n)
                    after_sorted_sd = partial.sorted_n[sd]
                    after_sorted_so = partial.sorted_n[so]
                    after_ub_sd = partial.ub(sd)
                    after_ub_so = partial.ub(so)
                    after_ub_total = after_ub_sd + after_ub_so

                # Prefer moves that keep the destination well placed, but never
                # return an empty set: if no such move exists, rank the least harmful
                # move by the actual post-move structure.
                priority = (
                    0 if compatible_dest else 1,
                    after_bad,
                    -after_sorted_total,
                    after_ub_total,
                    -after_sorted_sd,
                    -after_sorted_so,
                    0 if dest_sorted else 1,
                    0 if not dest_empty else 1,
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
