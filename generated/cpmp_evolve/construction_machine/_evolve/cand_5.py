COMPONENT = {'name': 'repair_priority_unlock_sorted_dest_balance', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 14.0}, 'score_k4': {'type': 'float', 'range': [0.0, 30.0], 'default': 6.0}, 'score_k5': {'type': 'float', 'range': [0.0, 30.0], 'default': 4.0}, 'score_k6': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.8}}}
from core.machine import FALLBACK

class RepairPriorityUnlockSortedDestBalance:
    _auto_score_k1 = 90.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 14.0
    _auto_score_k4 = 6.0
    _auto_score_k5 = 4.0
    _auto_score_k6 = 0.8
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
        bad_before = partial.bad()
        ub_before_source = partial.ub(action.so)
        ub_after_source = sim.ub(action.so)
        source_gain = ub_before_source - ub_after_source
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix = sim.sorted_n[action.sd]
        dest_height = sim.h(action.sd)
        source_height = partial.h(action.so)
        bad_drop = bad_before - bad_after
        return bad_after * self._auto_score_k1 - bad_drop * self._auto_score_k2 - source_gain * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - dest_prefix * self._auto_score_k5 + dest_height * self._auto_score_k6 - source_height * self._auto_score_k6

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityUnlockSortedDestBalance(problem)
_MACHINE = RepairPriorityUnlockSortedDestBalance
_AUTO = {'score_k1': 90.0, 'score_k2': 18.0, 'score_k3': 14.0, 'score_k4': 6.0, 'score_k5': 4.0, 'score_k6': 0.8}

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
