COMPONENT = {'name': 'repair_priority_sorted_progress_score', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k3': {'type': 'float', 'range': [0.0, 100.0], 'default': 18.0}, 'score_k4': {'type': 'float', 'range': [0.0, 100.0], 'default': 8.0}, 'score_k5': {'type': 'float', 'range': [0.0, 50.0], 'default': 3.0}}}
from core.machine import FALLBACK

class RepairPrioritySortedProgressScore:
    _auto_score_k1 = 120.0
    _auto_score_k2 = 25.0
    _auto_score_k3 = 18.0
    _auto_score_k4 = 8.0
    _auto_score_k5 = 3.0
    _auto_score_k6 = 1.0
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
        total_sorted_before = sum(partial.sorted_n)
        total_sorted_after = sum(sim.sorted_n)
        sorted_gain = total_sorted_after - total_sorted_before
        dest_gain = sim.sorted_n[action.sd] - partial.sorted_n[action.sd]
        source_loss = partial.sorted_n[action.so] - sim.sorted_n[action.so]
        source_ub_before = partial.ub(action.so)
        source_ub_after = sim.ub(action.so)
        dest_ub_after = sim.ub(action.sd)
        source_height = partial.h(action.so)
        dest_height = sim.h(action.sd)
        source_sorted = 1 if partial.is_sorted_stack(action.so) else 0
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        return bad_after * self._auto_score_k1 - sorted_gain * self._auto_score_k2 - dest_gain * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 + source_loss * self._auto_score_k4 + source_sorted * self._auto_score_k5 + source_ub_after * self._auto_score_k5 + dest_ub_after * self._auto_score_k6 + source_height * self._auto_score_k6 - source_ub_before * self._auto_score_k6 - partial.sorted_n[action.so] * self._auto_score_k6

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPrioritySortedProgressScore(problem)
_MACHINE = RepairPrioritySortedProgressScore
_AUTO = {'score_k1': 120.0, 'score_k2': 25.0, 'score_k3': 18.0, 'score_k4': 8.0, 'score_k5': 3.0, 'score_k6': 1.0, 'fallback_bad_threshold': 2}

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
