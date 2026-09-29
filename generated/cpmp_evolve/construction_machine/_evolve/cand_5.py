COMPONENT = {'name': 'safe_placement_refined_v4', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_placement_score_w_bad': {'type': 'int', 'range': [1, 10000000], 'default': 100000}, 'safe_placement_score_w_source_sorted': {'type': 'int', 'range': [0, 1000000], 'default': 1000000}, 'safe_placement_score_w_dest_nonempty': {'type': 'int', 'range': [0, 1000000], 'default': 1}}}
from core.rules import RuleMachine

class SafePlacementRule:
    name = 'safe_placement'
    priority = 100

    def __init__(self, safe_placement_score_w_bad=100000, safe_placement_score_w_source_sorted=1000000, safe_placement_score_w_dest_sorted=10000, safe_placement_score_w_source_ub=100, safe_placement_score_w_dest_nonempty=1):
        self._auto_safe_placement_score_w_bad = safe_placement_score_w_bad
        self._auto_safe_placement_score_w_source_sorted = safe_placement_score_w_source_sorted
        self._auto_safe_placement_score_w_dest_sorted = safe_placement_score_w_dest_sorted
        self._auto_safe_placement_score_w_source_ub = safe_placement_score_w_source_ub
        self._auto_safe_placement_score_w_dest_nonempty = safe_placement_score_w_dest_nonempty

    def init(self, partial):
        return ()

    def _eval(self, partial, action):
        tmp = partial.copy(track=False)
        tmp.move(action.so, action.sd)
        after_bad = tmp.bad()
        source_sorted_after = 0 if tmp.is_sorted_stack(action.so) else 1
        dest_sorted_after = 0 if tmp.is_sorted_stack(action.sd) else 1
        source_ub_after = tmp.ub(action.so)
        dest_nonempty = 1 if partial.h(action.sd) > 0 else 0
        score = after_bad * self._auto_safe_placement_score_w_bad + source_sorted_after * self._auto_safe_placement_score_w_source_sorted + dest_sorted_after * self._auto_safe_placement_score_w_dest_sorted + source_ub_after * self._auto_safe_placement_score_w_source_ub + dest_nonempty * self._auto_safe_placement_score_w_dest_nonempty
        return (after_bad, float(score))

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        best_bad = None
        kept = []
        for action in candidates:
            after_bad, _ = self._eval(partial, action)
            if best_bad is None or after_bad < best_bad:
                best_bad = after_bad
                kept = [action]
            elif after_bad == best_bad:
                kept.append(action)
        return sorted(kept, key=lambda a: self.score(partial, memory, a))

    def score(self, partial, memory, action):
        _, score = self._eval(partial, action)
        return score

def build_component(problem, **params):
    return RuleMachine(problem, [SafePlacementRule(**params)])
