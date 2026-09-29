COMPONENT = {'name': 'good_place_refined_rule_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from collections import namedtuple
from core.rules import FALLBACK, RuleMachine
Move = namedtuple('Move', ['so', 'sd'])

class GoodPlaceRule:
    name = 'good_place'

    def __init__(self, problem, prefer_non_empty: bool=True, prefer_sorted_dest: bool=True, prefer_tighter_fit: bool=True, source_bad_weight: float=1.0, dest_bad_weight: float=1.0, empty_penalty: float=1.0):
        self.problem = problem
        self.prefer_non_empty = prefer_non_empty
        self.prefer_sorted_dest = prefer_sorted_dest
        self.prefer_tighter_fit = prefer_tighter_fit
        self.source_bad_weight = float(source_bad_weight)
        self.dest_bad_weight = float(dest_bad_weight)
        self.empty_penalty = float(empty_penalty)

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
        total_bad = partial.bad()
        for so in range(n_stacks):
            if not partial.stacks[so]:
                continue
            c = partial.stacks[so][-1]
            source_bad = partial.ub(so)
            src_sorted = partial.is_sorted_stack(so)
            for sd in range(n_stacks):
                if not partial.valid(so, sd):
                    continue
                dest_empty = len(partial.stacks[sd]) == 0
                dest_sorted = partial.is_sorted_stack(sd)
                dest_top = partial.g(sd)
                if not dest_empty and c > dest_top:
                    allow = source_bad > 0 or total_bad > 0
                    if not allow:
                        continue
                try:
                    cp = partial.copy(track=False)
                    cp.move(so, sd)
                    after_bad = cp.bad()
                    after_sorted = cp.sorted_n[sd]
                    after_ub = cp.ub(sd)
                    dest_height = cp.h(sd)
                    src_height_after = cp.h(so)
                    dest_top_after = cp.g(sd)
                except Exception:
                    after_bad = total_bad
                    after_sorted = partial.sorted_n[sd]
                    after_ub = partial.ub(sd)
                    dest_height = len(partial.stacks[sd]) + 1
                    src_height_after = max(0, len(partial.stacks[so]) - 1)
                    dest_top_after = c
                fit_gap = 0 if dest_empty else max(0, dest_top_after - c)
                source_pressure = source_bad * self.source_bad_weight + max(0, src_sorted - source_bad)
                dest_penalty = after_ub * self.dest_bad_weight
                empty_bias = self.empty_penalty if dest_empty else 0.0
                priority = (0 if self.prefer_sorted_dest and dest_sorted and (dest_empty or c <= dest_top) else 1, 0 if self.prefer_non_empty and (not dest_empty) else 1, after_bad + dest_penalty + empty_bias, -after_sorted, after_ub, fit_gap if self.prefer_tighter_fit else 0, source_pressure, dest_height, src_height_after, c, so, sd)
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
    defaults = {'prefer_non_empty': True, 'prefer_sorted_dest': True, 'prefer_tighter_fit': True, 'source_bad_weight': 1.0, 'dest_bad_weight': 1.0, 'empty_penalty': 1.0}
    cfg = dict(defaults)
    cfg.update(params)
    rule = GoodPlaceRule(problem, prefer_non_empty=cfg['prefer_non_empty'], prefer_sorted_dest=cfg['prefer_sorted_dest'], prefer_tighter_fit=cfg['prefer_tighter_fit'], source_bad_weight=cfg['source_bad_weight'], dest_bad_weight=cfg['dest_bad_weight'], empty_penalty=cfg['empty_penalty'])
    trans = GreedyGoodPlaceTransitions(rule.name)
    return RuleMachine(problem, [rule], trans)
