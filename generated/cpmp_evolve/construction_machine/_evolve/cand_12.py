COMPONENT = {'name': 'repair_priority_finish_dest_fit_source_relief', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 80.0}, 'score_k2': {'type': 'float', 'range': [0.0, 80.0], 'default': 20.0}, 'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 15.0}, 'finish_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2}}}
from core.machine import FALLBACK

class RepairPriorityFinishDestFitSourceRelief:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 20.0
    _auto_score_k3 = 15.0
    _auto_finish_dest_bonus = 12.0
    _auto_finish_source_penalty = 4.0
    _auto_finish_ub_penalty = 18.0
    _auto_finish_dest_height_penalty = 0.5
    _auto_finish_source_height_penalty = 0.25
    _auto_finish_sorted_prefix_bonus = 20.0
    _auto_finish_bad_threshold = 2
    states = ('finish', 'repair')

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('finish', (partial.bad(),))

    def transition(self, partial, state, memory):
        bad = partial.bad()
        if partial.is_sorted():
            return (FALLBACK, ())
        if state == 'finish':
            return ('repair', memory)
        if state == 'repair':
            if bad <= self._auto_finish_bad_threshold:
                return ('finish', memory)
            return ('repair', memory)
        return (FALLBACK, ())

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
        if state == 'finish':
            return bad_after * self._auto_score_k1 + ub_after_source * self._auto_finish_ub_penalty - dest_sorted_gain * self._auto_finish_dest_bonus - dest_prefix * self._auto_finish_sorted_prefix_bonus + ub_before_source * self._auto_score_k3 + source_height * self._auto_finish_source_penalty + dest_height * self._auto_finish_dest_height_penalty + source_height * self._auto_finish_source_height_penalty
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_finish_dest_bonus - dest_prefix * self._auto_score_k2 + dest_height * self._auto_finish_dest_height_penalty - source_height * self._auto_finish_source_height_penalty

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityFinishDestFitSourceRelief(problem)
_MACHINE = RepairPriorityFinishDestFitSourceRelief
_AUTO = {'score_k1': 80.0, 'score_k2': 20.0, 'score_k3': 15.0, 'finish_dest_bonus': 12.0, 'finish_source_penalty': 4.0, 'finish_ub_penalty': 18.0, 'finish_dest_height_penalty': 0.5, 'finish_source_height_penalty': 0.25, 'finish_sorted_prefix_bonus': 20.0, 'finish_bad_threshold': 2}

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
