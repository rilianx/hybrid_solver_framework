COMPONENT = {'name': 'safe_relocate_greedy_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_height_weight': {'type': 'float', 'default': 0.2, 'range': [0.0, 5.0]}}}
from core.rules import RuleMachine

class SafeRelocateGreedyRefined:
    name = 'safe_relocate_greedy'
    priority = 100

    def __init__(self, prefer_sorted_support: bool=True, prefer_repair_source: bool=True, source_bad_weight: float=8.0, dest_bad_weight: float=4.0, unlock_weight: float=2.0, sorted_support_bonus: float=3.0, tight_support_bonus: float=1.5, empty_dest_bonus: float=0.8, source_height_weight: float=0.2, dest_height_weight: float=0.1, tie_so_weight: float=0.0001, tie_sd_weight: float=1e-05):
        self.prefer_sorted_support = prefer_sorted_support
        self.prefer_repair_source = prefer_repair_source
        self.source_bad_weight = source_bad_weight
        self.dest_bad_weight = dest_bad_weight
        self.unlock_weight = unlock_weight
        self.sorted_support_bonus = sorted_support_bonus
        self.tight_support_bonus = tight_support_bonus
        self.empty_dest_bonus = empty_dest_bonus
        self.source_height_weight = source_height_weight
        self.dest_height_weight = dest_height_weight
        self.tie_so_weight = tie_so_weight
        self.tie_sd_weight = tie_sd_weight

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        return list(candidates)

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        source_bad = float(partial.ub(so))
        dest_bad = float(partial.ub(sd))
        source_top = partial.g(so)
        dest_top = partial.g(sd)
        source_sorted = bool(partial.is_sorted_stack(so))
        dest_sorted = bool(partial.is_sorted_stack(sd))
        source_h = float(partial.h(so))
        dest_h = float(partial.h(sd))
        nxt = partial.copy(track=False)
        nxt.move(so, sd)
        new_bad = float(nxt.bad())
        new_ub = float(sum((nxt.ub(i) for i in range(nxt.S))))
        support_ok = 1.0 if dest_sorted and source_top <= dest_top else 0.0
        tight_support = 1.0 if dest_sorted and (dest_h > 0 or partial.h(sd) == 0) else 0.0
        empty_dest = 1.0 if partial.h(sd) == 0 else 0.0
        repair_source = 1.0 if source_bad > 0 else 0.0
        score = 0.0
        score += 1000000.0 * new_bad
        score += 10000.0 * new_ub
        score += self.source_bad_weight * source_bad
        score += self.dest_bad_weight * dest_bad
        if self.prefer_repair_source:
            score -= self.unlock_weight * repair_source
        if self.prefer_sorted_support:
            score -= self.sorted_support_bonus * support_ok
            score -= self.tight_support_bonus * tight_support
        score -= self.empty_dest_bonus * empty_dest
        score += self.source_height_weight * source_h
        score += self.dest_height_weight * dest_h
        score += self.tie_so_weight * float(so)
        score += self.tie_sd_weight * float(sd)
        return score

    def update(self, partial, memory, action):
        return memory

def build_component(problem, **params):
    return RuleMachine(problem, [SafeRelocateGreedyRefined(**params)])
