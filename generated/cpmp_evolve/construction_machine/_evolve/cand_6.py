COMPONENT = {'name': 'good_place_repaired_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from collections import namedtuple
from core.rules import FALLBACK, RuleMachine
Move = namedtuple('Move', ['so', 'sd'])

class GoodPlaceRule:
    name = 'good_place'

    def __init__(self, problem, prefer_sorted_dest: bool=True, prefer_non_empty: bool=True, prefer_tighter_fit: bool=True, source_bad_weight: float=1.0, dest_bad_weight: float=1.0, keep_sorted_bonus: float=1.0):
        self.problem = problem
        self.prefer_sorted_dest = prefer_sorted_dest
        self.prefer_non_empty = prefer_non_empty
        self.prefer_tighter_fit = prefer_tighter_fit
        self.source_bad_weight = float(source_bad_weight)
        self.dest_bad_weight = float(dest_bad_weight)
        self.keep_sorted_bonus = float(keep_sorted_bonus)

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        return memory

    def update(self, partial, memory, action):
        return memory

    def done(self, partial, memory):
        return True

    def _safe_sim(self, partial, so, sd, c):
        try:
            cp = partial.copy(track=False)
            cp.move(so, sd)
            return (cp.bad(), cp.sorted_n[sd], cp.ub(sd), cp.h(sd), cp.h(so), cp.g(sd), cp.sorted_n[so])
        except Exception:
            dest_empty = len(partial.stacks[sd]) == 0
            dest_top = partial.g(sd) if not dest_empty else c
            src_height = max(0, len(partial.stacks[so]) - 1)
            dest_height = len(partial.stacks[sd]) + 1
            after_bad = partial.bad()
            after_sorted = partial.sorted_n[sd]
            after_ub = partial.ub(sd)
            src_sorted = partial.sorted_n[so]
            return (after_bad, after_sorted, after_ub, dest_height, src_height, dest_top, src_sorted)

    def propose(self, partial, memory):
        moves = []
        n_stacks = partial.S
        for so in range(n_stacks):
            if not partial.stacks[so]:
                continue
            c = partial.stacks[so][-1]
            source_bad = partial.ub(so)
            source_sorted_before = partial.sorted_n[so]
            source_height = partial.h(so)
            for sd in range(n_stacks):
                if not partial.valid(so, sd):
                    continue
                dest_empty = len(partial.stacks[sd]) == 0
                dest_sorted = partial.is_sorted_stack(sd)
                dest_top = partial.g(sd)
                dest_height = partial.h(sd)
                after_bad, after_sorted, after_ub, sim_dest_height, sim_src_height, sim_dest_top, sim_src_sorted = self._safe_sim(partial, so, sd, c)
                fits = dest_empty or c <= dest_top
                makes_sorted_dest = dest_empty or (dest_sorted and c <= dest_top)
                preserves_source_sorted = source_sorted_before == source_height or source_sorted_before <= max(0, source_height - 1)
                fit_gap = 0 if dest_empty else max(0, dest_top - c)
                src_loss = max(0, source_bad - after_bad)
                dest_gain = max(0, after_sorted - partial.sorted_n[sd])
                priority = (0 if self.prefer_sorted_dest and makes_sorted_dest else 1, 0 if self.prefer_non_empty and (not dest_empty) else 1, after_bad, -dest_gain, -after_sorted, after_ub, -src_loss * self.source_bad_weight, 0 if preserves_source_sorted else 1, fit_gap if self.prefer_tighter_fit else 0, -self.keep_sorted_bonus if dest_sorted and fits else 0, sim_dest_height, sim_src_height, dest_height, source_height, c, so, sd)
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
    defaults = {'prefer_sorted_dest': True, 'prefer_non_empty': True, 'prefer_tighter_fit': True, 'source_bad_weight': 1.0, 'dest_bad_weight': 1.0, 'keep_sorted_bonus': 1.0}
    cfg = dict(defaults)
    cfg.update(params)
    rule = GoodPlaceRule(problem, prefer_sorted_dest=cfg['prefer_sorted_dest'], prefer_non_empty=cfg['prefer_non_empty'], prefer_tighter_fit=cfg['prefer_tighter_fit'], source_bad_weight=cfg['source_bad_weight'], dest_bad_weight=cfg['dest_bad_weight'], keep_sorted_bonus=cfg['keep_sorted_bonus'])
    trans = GreedyGoodPlaceTransitions(rule.name)
    return RuleMachine(problem, [rule], trans)
