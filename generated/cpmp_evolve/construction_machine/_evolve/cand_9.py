COMPONENT = {'name': 'good_place_fallback_guard_transition_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'use_rule_if_sorted_destinations': {'type': 'bool', 'default': True}, 'max_bad_to_use_rule': {'type': 'int', 'range': [0, 100], 'default': 2}, 'max_ub_to_use_rule': {'type': 'int', 'range': [0, 100], 'default': 100}}}
from core.rules import FALLBACK, RuleMachine

class GoodPlaceRule:
    name = 'good_place'

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
                can_be_well_placed = dest_empty or c <= partial.g(sd)
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
                priority = (0 if dest_sorted else 1, 0 if not dest_empty else 1, after_bad, -after_sorted, after_ub, so, sd)
                moves.append((priority, (so, sd)))
        moves.sort(key=lambda x: x[0])
        return [m for _, m in moves]

class GuardedGoodPlaceTransitions:

    def __init__(self, rule_name: str, use_rule_if_sorted_destinations: bool=True, use_rule_if_empty_destination: bool=False, max_bad_to_use_rule: int=2, max_ub_to_use_rule: int=100, prefer_rule_when_single_candidate: bool=False):
        self.rule_name = rule_name
        self.use_rule_if_sorted_destinations = use_rule_if_sorted_destinations
        self.use_rule_if_empty_destination = use_rule_if_empty_destination
        self.max_bad_to_use_rule = max_bad_to_use_rule
        self.max_ub_to_use_rule = max_ub_to_use_rule
        self.prefer_rule_when_single_candidate = prefer_rule_when_single_candidate

    def initial(self, partial):
        return ()

    def _has_sorted_destination(self, partial) -> bool:
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.stacks[so][-1]
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                if partial.is_sorted_stack(sd) and c <= partial.g(sd):
                    return True
        return False

    def _has_empty_destination(self, partial) -> bool:
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.stacks[so][-1]
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                if len(partial.stacks[sd]) == 0 and c <= partial.g(sd):
                    return True
        return False

    def _candidate_pressure(self, partial) -> tuple[int, int]:
        bad = partial.bad()
        ub = 0
        for i in range(partial.S):
            ub += partial.ub(i)
        return (bad, ub)

    def select(self, partial, memory, rules):
        if not rules.applies(self.rule_name):
            return (FALLBACK, memory)
        bad, ub = self._candidate_pressure(partial)
        if bad > self.max_bad_to_use_rule or ub > self.max_ub_to_use_rule:
            return (FALLBACK, memory)
        if self.use_rule_if_sorted_destinations and self._has_sorted_destination(partial):
            return (self.rule_name, memory)
        if self.use_rule_if_empty_destination and self._has_empty_destination(partial):
            return (self.rule_name, memory)
        if self.prefer_rule_when_single_candidate:
            n_moves = 0
            for so in range(partial.S):
                if not partial.stacks[so]:
                    continue
                for sd in range(partial.S):
                    if partial.valid(so, sd):
                        n_moves += 1
                        if n_moves > 1:
                            break
                if n_moves > 1:
                    break
            if n_moves == 1:
                return (self.rule_name, memory)
        return (FALLBACK, memory)

def build_component(problem, **params):
    rule = GoodPlaceRule(problem)
    trans = GuardedGoodPlaceTransitions(rule.name, use_rule_if_sorted_destinations=params.get('use_rule_if_sorted_destinations', True), use_rule_if_empty_destination=params.get('use_rule_if_empty_destination', False), max_bad_to_use_rule=params.get('max_bad_to_use_rule', 2), max_ub_to_use_rule=params.get('max_ub_to_use_rule', 100), prefer_rule_when_single_candidate=params.get('prefer_rule_when_single_candidate', False))
    return RuleMachine(problem, [rule], trans)
