COMPONENT = {'name': 'repair_priority_reduce_bad_with_safe_dest', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k2': {'type': 'float', 'range': [0.0, 80.0], 'default': 18.0}, 'score_k4': {'type': 'float', 'range': [0.0, 40.0], 'default': 6.0}, 'score_k6': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}, 'score_k7': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.25}}}
from core.machine import FALLBACK

class RepairPriorityReduceBadWithSafeDest:
    _auto_score_k1 = 90.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 12.0
    _auto_score_k4 = 6.0
    _auto_score_k5 = 1.0
    _auto_score_k6 = 0.5
    _auto_score_k7 = 0.25
    _auto_fallback_bad_threshold = 2
    states = ('repair',)

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('repair', (partial.bad(),))

    def transition(self, partial, state, memory):
        if partial.is_sorted() and partial.bad() <= self._auto_fallback_bad_threshold:
            return (FALLBACK, ())
        return ('repair', memory)

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        sim.move(action.so, action.sd)
        bad_after = sim.bad()
        bad_before = partial.bad()
        ub_before_source = partial.ub(action.so)
        ub_after_source = sim.ub(action.so)
        source_delta = ub_after_source - ub_before_source
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix_before = partial.sorted_n[action.sd]
        dest_prefix_after = sim.sorted_n[action.sd]
        dest_prefix_gain = dest_prefix_after - dest_prefix_before
        dest_height = sim.h(action.sd)
        dest_free = sim.e(action.sd)
        source_height = partial.h(action.so)
        bad_gain = bad_before - bad_after
        return bad_after * self._auto_score_k1 + source_delta * self._auto_score_k2 - bad_gain * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - dest_prefix_gain * self._auto_score_k5 + dest_height * self._auto_score_k6 - dest_free * self._auto_score_k7 + source_height * self._auto_score_k7

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityReduceBadWithSafeDest(problem)
_MACHINE = RepairPriorityReduceBadWithSafeDest
_AUTO = {'score_k1': 90.0, 'score_k2': 18.0, 'score_k3': 12.0, 'score_k4': 6.0, 'score_k5': 1.0, 'score_k6': 0.5, 'score_k7': 0.25, 'fallback_bad_threshold': 2}

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
