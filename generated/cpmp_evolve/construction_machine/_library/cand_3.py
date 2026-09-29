COMPONENT = {'name': 'safe_sorted_destination_rule_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'prefer_empty': {'type': 'bool', 'default': True}, 'empty_bonus': {'type': 'float', 'range': [-10.0, 10.0], 'default': -1.0}, 'top_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}, 'sorted_bonus': {'type': 'float', 'range': [-10.0, 10.0], 'default': -1.0}, 'nonempty_bonus': {'type': 'float', 'range': [-10.0, 10.0], 'default': 0.0}}}
from core.rules import RuleMachine

class SafeSortedDestinationRule:
    name = 'safe_sorted_destination_rule'

    def __init__(self, prefer_empty=True, empty_bonus=-1.0, top_weight=1.0, sorted_bonus=-1.0, same_group_bonus=-1.0, nonempty_bonus=0.0):
        self.prefer_empty = prefer_empty
        self.empty_bonus = empty_bonus
        self.top_weight = top_weight
        self.sorted_bonus = sorted_bonus
        self.same_group_bonus = same_group_bonus
        self.nonempty_bonus = nonempty_bonus

    def _score(self, partial, a):
        sd = a.sd
        so = a.so
        dest_h = partial.h(sd)
        src_top = partial.g(so)
        dest_top = partial.g(sd)
        score = float(dest_top) * self.top_weight
        if dest_h == 0:
            if self.prefer_empty:
                score += self.empty_bonus
        else:
            score += self.nonempty_bonus
            if partial.is_sorted_stack(sd):
                score += self.sorted_bonus
            if dest_top == src_top:
                score += self.same_group_bonus
        return score

    def allowed(self, partial, memory, candidates):
        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0:
                continue
            if partial.h(sd) >= partial.H:
                continue
            allowed.append(a)
        allowed.sort(key=lambda a: (self._score(partial, a), a.sd, a.so))
        return allowed

def build_component(problem, **params):
    return RuleMachine(problem, [SafeSortedDestinationRule(prefer_empty=params.get('prefer_empty', True), empty_bonus=params.get('empty_bonus', -1.0), top_weight=params.get('top_weight', 1.0), sorted_bonus=params.get('sorted_bonus', -1.0), same_group_bonus=params.get('same_group_bonus', -1.0), nonempty_bonus=params.get('nonempty_bonus', 0.0))])
