COMPONENT = {'name': 'good_place_refined_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from collections import namedtuple
from core.rules import FALLBACK, RuleMachine
Move = namedtuple('Move', ['so', 'sd'])

class GoodPlaceRule:
    name = 'good_place'

    def __init__(self, problem, prefer_non_empty: bool=True, prefer_sorted_dest: bool=True, prefer_tighter_fit: bool=True, source_bad_weight: float=1.0):
        self.problem = problem
        self.prefer_non_empty = prefer_non_empty
        self.prefer_sorted_dest = prefer_sorted_dest
        self.prefer_tighter_fit = prefer_tighter_fit
        self.source_bad_weight = float(source_bad_weight)

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
            source_bad = partial.ub(so)
            for sd in range(n_stacks):
                if not partial.valid(so, sd):
                    continue
                dest_empty = len(partial.stacks[sd]) == 0
                dest_sorted = partial.is_sorted_stack(sd)
                if not (dest_empty or c <= partial.g(sd)):
                    continue
                try:
                    cp = partial.copy(track=False)
                    cp.move(so, sd)
                    after_bad = cp.bad()
                    after_sorted = cp.sorted_n[sd]
                    after_ub = cp.ub(sd)
                    dest_height = cp.h(sd)
                    src_height = cp.h(so)
                    dest_top = cp.g(sd)
                except Exception:
                    after_bad = partial.bad()
                    after_sorted = partial.sorted_n[sd]
                    after_ub = partial.ub(sd)
                    dest_height = len(partial.stacks[sd]) + 1
                    src_height = max(0, len(partial.stacks[so]) - 1)
                    dest_top = c
                fit_gap = 0 if dest_empty else max(0, dest_top - c)
                priority = (0 if self.prefer_sorted_dest and dest_sorted else 1, 0 if self.prefer_non_empty and (not dest_empty) else 1, after_bad, -after_sorted, after_ub, fit_gap if self.prefer_tighter_fit else 0, -source_bad * self.source_bad_weight, dest_height, src_height, c, so, sd)
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
            return (self.rule_name, memory)
        return (FALLBACK, memory)

def build_component(problem, **params):
    defaults = {'prefer_non_empty': True, 'prefer_sorted_dest': True, 'prefer_tighter_fit': True, 'source_bad_weight': 1.0}
    cfg = dict(defaults)
    cfg.update(params)
    rule = GoodPlaceRule(problem, prefer_non_empty=cfg['prefer_non_empty'], prefer_sorted_dest=cfg['prefer_sorted_dest'], prefer_tighter_fit=cfg['prefer_tighter_fit'], source_bad_weight=cfg['source_bad_weight'])
    trans = GreedyGoodPlaceTransitions(rule.name)
    return RuleMachine(problem, [rule], trans)
