COMPONENT = {'name': 'repair_priority_unlocking_score', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 80.0}, 'score_k2': {'type': 'float', 'range': [0.0, 80.0], 'default': 20.0}, 'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 15.0}, 'score_k4': {'type': 'float', 'range': [0.0, 20.0], 'default': 3.0}, 'score_k6': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}}}
from core.machine import FALLBACK

class RepairPriorityUnlockingScore:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 20.0
    _auto_score_k3 = 15.0
    _auto_score_k4 = 3.0
    _auto_score_k5 = 2.0
    _auto_score_k6 = 0.5
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
        ub_after_source = sim.ub(action.so)
        ub_after_dest = sim.ub(action.sd)
        ub_total_after = 0
        for i in range(sim.S):
            ub_total_after += sim.ub(i)
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        source_height = partial.h(action.so)
        dest_height = sim.h(action.sd)
        source_top = partial.g(action.so)
        dest_top_before = partial.g(action.sd)
        return bad_after * self._auto_score_k1 + ub_total_after * self._auto_score_k2 + ub_after_source * self._auto_score_k3 + ub_after_dest * self._auto_score_k4 - dest_sorted_gain * self._auto_score_k5 + max(0, source_top - dest_top_before) * self._auto_score_k6 + dest_height * self._auto_score_k6 - source_height * self._auto_score_k6

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityUnlockingScore(problem)
_MACHINE = RepairPriorityUnlockingScore
_AUTO = {'score_k1': 80.0, 'score_k2': 20.0, 'score_k3': 15.0, 'score_k4': 3.0, 'score_k5': 2.0, 'score_k6': 0.5, 'fallback_bad_threshold': 2}

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
