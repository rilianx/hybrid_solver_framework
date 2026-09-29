COMPONENT = {'name': 'repair_priority_refine_source_dest_balance', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 90.0}, 'score_k2': {'type': 'float', 'range': [0.0, 100.0], 'default': 18.0}, 'score_k3': {'type': 'float', 'range': [0.0, 100.0], 'default': 10.0}, 'score_k4': {'type': 'float', 'range': [0.0, 50.0], 'default': 6.0}}}
from core.machine import FALLBACK

class RepairPriorityRefineSourceDestBalance:
    _auto_score_k1 = 90.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 10.0
    _auto_score_k4 = 6.0
    _auto_score_k5 = 2.0
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
        source_bad_after = sim.ub(action.so)
        source_sorted_before = 1 if partial.is_sorted_stack(action.so) else 0
        source_sorted_after = 1 if sim.is_sorted_stack(action.so) else 0
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix_after = sim.sorted_n[action.sd]
        dest_top_after = sim.g(action.sd)
        moved_group = partial.g(action.so)
        return bad_after * self._auto_score_k1 + source_bad_after * self._auto_score_k2 - source_sorted_after * self._auto_score_k3 + source_sorted_before * self._auto_score_k4 - dest_sorted_gain * self._auto_score_k5 - dest_prefix_after * self._auto_score_k2 - dest_top_after * self._auto_score_k6 + moved_group * self._auto_score_k6

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityRefineSourceDestBalance(problem)
_MACHINE = RepairPriorityRefineSourceDestBalance
_AUTO = {'score_k1': 90.0, 'score_k2': 18.0, 'score_k3': 10.0, 'score_k4': 6.0, 'score_k5': 2.0, 'score_k6': 1.0, 'fallback_bad_threshold': 2}

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
