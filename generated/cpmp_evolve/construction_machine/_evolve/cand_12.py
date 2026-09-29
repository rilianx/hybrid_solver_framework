COMPONENT = {'name': 'repair_priority_refined_source_destination_score', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 100.0}, 'score_k2': {'type': 'float', 'range': [0.0, 120.0], 'default': 30.0}, 'score_k3': {'type': 'float', 'range': [0.0, 120.0], 'default': 25.0}, 'score_k4': {'type': 'float', 'range': [0.0, 80.0], 'default': 8.0}, 'score_k5': {'type': 'float', 'range': [0.0, 80.0], 'default': 6.0}, 'score_k6': {'type': 'float', 'range': [0.0, 40.0], 'default': 2.0}, 'fallback_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2}}}
from core.machine import FALLBACK

class RepairPriorityRefinedSourceDestinationScore:
    _auto_score_k7 = 0.5
    _auto_score_k8 = 0.25
    _auto_score_k1 = 100.0
    _auto_score_k2 = 30.0
    _auto_score_k3 = 25.0
    _auto_score_k4 = 8.0
    _auto_score_k5 = 6.0
    _auto_score_k6 = 2.0
    _auto_fallback_bad_threshold = 2
    states = ('repair',)

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('repair', (partial.bad(),))

    def transition(self, partial, state, memory):
        bad_now = partial.bad()
        if partial.is_sorted() and bad_now <= self._auto_fallback_bad_threshold:
            return (FALLBACK, ())
        if bad_now <= self._auto_fallback_bad_threshold:
            return (FALLBACK, ())
        return ('repair', memory)

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        so, sd = (action.so, action.sd)
        c = partial.g(so)
        dest_top_before = partial.g(sd)
        src_sorted_before = 1 if partial.is_sorted_stack(so) else 0
        dest_sorted_before = 1 if partial.is_sorted_stack(sd) else 0
        src_ub_before = partial.ub(so)
        dest_ub_before = partial.ub(sd)
        sim.move(so, sd)
        bad_after = sim.bad()
        src_ub_after = sim.ub(so)
        dest_ub_after = sim.ub(sd)
        dest_sorted_gain = (1 if sim.is_sorted_stack(sd) else 0) - dest_sorted_before
        src_ub_gain = src_ub_before - src_ub_after
        dest_ub_gain = dest_ub_before - dest_ub_after
        return bad_after * self._auto_score_k1 - src_ub_gain * self._auto_score_k2 - dest_sorted_gain * self._auto_score_k3 - dest_ub_gain * self._auto_score_k4 + dest_top_before * self._auto_score_k5 + src_sorted_before * self._auto_score_k6 + sim.h(sd) * self._auto_score_k7 - sim.h(so) * self._auto_score_k8

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem, **params):
    return RepairPriorityRefinedSourceDestinationScore(problem)
_MACHINE = RepairPriorityRefinedSourceDestinationScore
_AUTO = {'score_k1': 100.0, 'score_k2': 30.0, 'score_k3': 25.0, 'score_k4': 8.0, 'score_k5': 6.0, 'score_k6': 2.0, 'fallback_bad_threshold': 2, 'score_k7': 0.5, 'score_k8': 0.25}

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
