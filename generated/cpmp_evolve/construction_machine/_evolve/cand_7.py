COMPONENT = {'name': 'repair_priority_source_first_score', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 300.0], 'default': 120.0}, 'score_k2': {'type': 'float', 'range': [0.0, 120.0], 'default': 18.0}, 'score_k3': {'type': 'float', 'range': [0.0, 120.0], 'default': 8.0}, 'score_k5': {'type': 'float', 'range': [0.0, 40.0], 'default': 1.0}}}
from core.machine import FALLBACK

class RepairPrioritySourceFirstScore:
    _auto_score_k1 = 120.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 8.0
    _auto_score_k4 = 10.0
    _auto_score_k5 = 1.0
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
        c = sim.g(action.so)
        sim.move(action.so, action.sd)
        bad_after = sim.bad()
        source_ub_after = sim.ub(action.so)
        source_ub_before = partial.ub(action.so)
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix_after = sim.sorted_n[action.sd]
        dest_height = sim.h(action.sd)
        source_height_after = sim.h(action.so)
        return bad_after * self._auto_score_k1 + source_ub_after * self._auto_score_k2 + source_ub_before * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - dest_prefix_after * self._auto_score_k5 + dest_height * self._auto_score_k5 + source_height_after * self._auto_score_k5 + (0.0 if c >= partial.g(action.sd) else self._auto_score_k5)

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPrioritySourceFirstScore(problem)
_MACHINE = RepairPrioritySourceFirstScore
_AUTO = {'score_k1': 120.0, 'score_k2': 18.0, 'score_k3': 8.0, 'score_k4': 10.0, 'score_k5': 1.0, 'fallback_bad_threshold': 2}

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
