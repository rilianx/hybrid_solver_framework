COMPONENT = {
    "name": "good_place_rule_refined",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from collections import namedtuple

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

    def _priority(self, partial, so, sd):
        c = partial.stacks[so][-1]
        dest_empty = len(partial.stacks[sd]) == 0
        dest_sorted = partial.is_sorted_stack(sd)
        source_len = len(partial.stacks[so])
        source_sorted = partial.is_sorted_stack(so)

        cp = partial.copy(track=False)
        cp.move(so, sd)

        after_bad = cp.bad()
        after_sorted = cp.sorted_n[sd]
        after_ub = cp.ub(sd)

        # Penalize moves that disrupt a perfectly good singleton stack unless needed.
        singleton_penalty = 1 if (source_len == 1 and source_sorted) else 0

        # Prefer moves that place the container on an already sorted stack,
        # avoid empty destinations when a sorted support exists, and reduce bad blocks.
        return (
            after_bad,
            singleton_penalty,
            0 if dest_sorted else 1,
            0 if not dest_empty else 1,
            -after_sorted,
            after_ub,
            0 if c <= partial.g(sd) else 1,
            -partial.ub(so),
            so,
            sd,
        )

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

                # A good place is only meaningful if the container can be well placed
                # on an ordered support or on an empty stack.
                if not dest_empty and c > partial.g(sd):
                    continue

                try:
                    priority = self._priority(partial, so, sd)
                except Exception:
                    # Conservative fallback: still keep the move if it is valid and well-placed.
                    priority = (
                        partial.bad(),
                        1 if (len(partial.stacks[so]) == 1 and partial.is_sorted_stack(so)) else 0,
                        0 if dest_sorted else 1,
                        0 if not dest_empty else 1,
                        0,
                        0,
                        0,
                        0,
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
