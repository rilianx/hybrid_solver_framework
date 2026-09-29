COMPONENT = {'name': 'buffer_relocation_macro_v1', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
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

class BufferRelocationMacro:
    name = 'buffer_relocation'
    priority = 110

    def init(self, partial):
        return ()

    def _action_score(self, partial, action):
        tmp = partial.copy(track=False)
        tmp.move(action.so, action.sd)
        return float(tmp.bad() * 1000000 + sum((tmp.ub(i) for i in range(tmp.S))) * 100000 + (0 if tmp.is_sorted_stack(action.sd) else 1) * 1000 + (0 if tmp.is_sorted_stack(action.so) else 1))

    def start(self, partial, memory):
        candidates = []
        for d in range(partial.S):
            if partial.h(d) >= partial.H:
                continue
            if partial.h(d) > 0 and (not partial.is_sorted_stack(d)):
                continue
            dest_score = None
            for s in range(partial.S):
                if not partial.valid(s, d):
                    continue
                a = type('A', (), {'so': s, 'sd': d})()
                sc = self._action_score(partial, a)
                if dest_score is None or sc < dest_score:
                    dest_score = sc
            if dest_score is not None:
                candidates.append((dest_score, partial.h(d), d))
        if not candidates:
            return (-1,)
        candidates.sort()
        return (candidates[0][2],)

    def allowed(self, partial, memory, candidates):
        if not candidates or not memory or memory[0] < 0:
            return []
        d = memory[0]
        res = [a for a in candidates if a.sd == d]
        return sorted(res, key=lambda a: self.score(partial, memory, a))

    def score(self, partial, memory, action):
        return self._action_score(partial, action)

    def done(self, partial, memory):
        if not memory or memory[0] < 0:
            return True
        d = memory[0]
        if partial.h(d) >= partial.H:
            return True
        for s in range(partial.S):
            if partial.valid(s, d):
                return False
        return True

    def update(self, partial, memory, action):
        return memory

def build_component(problem, **params):
    return RuleMachine(problem, [BufferRelocationMacro(), SafePlacementRule(**params)])
