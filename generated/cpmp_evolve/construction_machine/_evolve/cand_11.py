COMPONENT = {'name': 'repair_priority_promote_fallback_on_stall_transition', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'stagnation_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 6}}}
from core.machine import FALLBACK

class RepairPriorityPromoteFallbackOnStallTransition:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 20.0
    _auto_score_k3 = 15.0
    _auto_score_k4 = 3.0
    _auto_score_k5 = 0.5
    _auto_fallback_bad_threshold = 2
    _auto_stagnation_bad_threshold = 6
    states = ('repair',)

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('repair', (partial.bad(),))

    def transition(self, partial, state, memory):
        current_bad = partial.bad()
        previous_bad = memory[0] if memory else current_bad
        if partial.is_sorted() and current_bad <= self._auto_fallback_bad_threshold:
            return (FALLBACK, ())
        if current_bad <= self._auto_stagnation_bad_threshold and current_bad >= previous_bad:
            return (FALLBACK, ())
        return ('repair', (current_bad,))

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        sim.move(action.so, action.sd)
        bad_after = sim.bad()
        ub_before_source = partial.ub(action.so)
        ub_after_source = sim.ub(action.so)
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix = sim.sorted_n[action.sd]
        source_height = partial.h(action.so)
        dest_height = sim.h(action.sd)
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - dest_prefix * self._auto_score_k2 + dest_height * self._auto_score_k5 - source_height * self._auto_score_k5

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityPromoteFallbackOnStallTransition(problem)
_MACHINE = RepairPriorityPromoteFallbackOnStallTransition
_AUTO = {'score_k1': 80.0, 'score_k2': 20.0, 'score_k3': 15.0, 'score_k4': 3.0, 'score_k5': 0.5, 'fallback_bad_threshold': 2, 'stagnation_bad_threshold': 6}

def build_component(problem, **params):
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    saved = {k: getattr(_MACHINE, '_auto_' + k) for k in auto}
    for k, v in auto.items():
        setattr(_MACHINE, '_auto_' + k, v)
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_MACHINE, '_auto_' + k, v)
    for k, v in auto.items():
        setattr(obj, '_auto_' + k, v)
    return obj
