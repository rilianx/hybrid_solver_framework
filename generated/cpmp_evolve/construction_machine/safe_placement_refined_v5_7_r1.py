COMPONENT = {'name': 'safe_placement_refined_v5', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_placement_score_w_total_ub': {'type': 'int', 'range': [0, 10000000], 'default': 100000}, 'safe_placement_score_w_dest_unsorted': {'type': 'int', 'range': [0, 1000000], 'default': 1000}, 'safe_placement_score_w_source_sorted': {'type': 'int', 'range': [0, 1000000], 'default': 0}}}
from core.rules import RuleMachine

class SafePlacementRule:
    name = 'safe_placement'
    priority = 100

    def __init__(self, safe_placement_score_w_bad=1000000, safe_placement_score_w_total_ub=100000, safe_placement_score_w_dest_unsorted=1000, safe_placement_score_w_source_sorted=0):
        self._auto_safe_placement_score_w_bad = safe_placement_score_w_bad
        self._auto_safe_placement_score_w_total_ub = safe_placement_score_w_total_ub
        self._auto_safe_placement_score_w_dest_unsorted = safe_placement_score_w_dest_unsorted
        self._auto_safe_placement_score_w_source_sorted = safe_placement_score_w_source_sorted

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        return sorted(candidates, key=lambda a: self.score(partial, memory, a))

    def score(self, partial, memory, action):
        tmp = partial.copy(track=False)
        tmp.move(action.so, action.sd)
        after_bad = tmp.bad()
        total_ub_after = sum((tmp.ub(i) for i in range(tmp.S)))
        dest_unsorted_after = 1 if not tmp.is_sorted_stack(action.sd) else 0
        source_sorted_after = 1 if tmp.is_sorted_stack(action.so) else 0
        return float(after_bad * self._auto_safe_placement_score_w_bad + total_ub_after * self._auto_safe_placement_score_w_total_ub + dest_unsorted_after * self._auto_safe_placement_score_w_dest_unsorted + source_sorted_after * self._auto_safe_placement_score_w_source_sorted)

def build_component(problem, **params):
    return RuleMachine(problem, [SafePlacementRule(**params)])
