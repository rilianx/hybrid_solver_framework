COMPONENT = {'name': 'repair_priority_unlock_and_fit', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k3': {'type': 'float', 'range': [0.0, 500.0], 'default': 20.0}, 'score_k4': {'type': 'float', 'range': [0.0, 50.0], 'default': 2.0}, 'score_k5': {'type': 'float', 'range': [0.0, 50.0], 'default': 1.0}, 'score_k6': {'type': 'float', 'range': [0.0, 0.2], 'default': 0.1}, 'score_k7': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.machine import FALLBACK

class RepairPriorityUnlockAndFit:
    _auto_score_k6 = 0.1
    _auto_score_k7 = 0.01
    _auto_score_k1 = 120.0
    _auto_score_k2 = 35.0
    _auto_score_k3 = 20.0
    _auto_score_k4 = 2.0
    _auto_score_k5 = 1.0
    states = ('repair',)

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        if partial.is_sorted():
            return (FALLBACK, ())
        return ('repair', (partial.bad(),))

    def transition(self, partial, state, memory):
        if partial.is_sorted():
            return (FALLBACK, ())
        return ('repair', memory)

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        sim.move(action.so, action.sd)
        bad_after = sim.bad()
        ub_after = sum((sim.ub(i) for i in range(sim.S)))
        ub_source = partial.ub(action.so)
        source_sorted = 1 if partial.is_sorted_stack(action.so) else 0
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        fit_gain = 1 if sim.sorted_n[action.sd] > partial.sorted_n[action.sd] else 0
        dest_height = sim.h(action.sd)
        source_height = sim.h(action.so)
        return bad_after * self._auto_score_k1 + ub_after * self._auto_score_k2 - ub_source * self._auto_score_k3 + source_sorted * self._auto_score_k4 + (1 - dest_sorted_after) * self._auto_score_k5 + (dest_sorted_before - dest_sorted_after) * self._auto_score_k4 - fit_gain * self._auto_score_k3 + dest_height * self._auto_score_k6 + source_height * self._auto_score_k7

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityUnlockAndFit(problem)
_MACHINE = RepairPriorityUnlockAndFit
_AUTO = {'score_k1': 120.0, 'score_k2': 35.0, 'score_k3': 20.0, 'score_k4': 2.0, 'score_k5': 1.0, 'score_k6': 0.1, 'score_k7': 0.01}

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
