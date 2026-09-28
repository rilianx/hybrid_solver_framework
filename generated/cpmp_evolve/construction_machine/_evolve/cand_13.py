COMPONENT = {'name': 'repair_priority_finish_unlock_sorted_bias', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 80.0}, 'score_k2': {'type': 'float', 'range': [0.0, 80.0], 'default': 20.0}, 'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 15.0}, 'finish_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2}, 'finish_source_penalty': {'type': 'float', 'range': [0.0, 20.0], 'default': 4.0}, 'finish_dest_sorted_bonus': {'type': 'float', 'range': [0.0, 30.0], 'default': 14.0}, 'finish_source_unlock_bonus': {'type': 'float', 'range': [0.0, 30.0], 'default': 10.0}}}
from core.machine import FALLBACK

class RepairPriorityFinishUnlockSortedBias:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 20.0
    _auto_score_k3 = 15.0
    _auto_score_k4 = 3.0
    _auto_score_k5 = 0.5
    _auto_finish_bad_threshold = 2
    _auto_finish_source_penalty = 4.0
    _auto_finish_dest_sorted_bonus = 14.0
    _auto_finish_source_unlock_bonus = 10.0
    _auto_finish_dest_fill_penalty = 2.5
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
        source_height = partial.h(action.so)
        dest_height = sim.h(action.sd)
        dest_slack_after = sim.e(action.sd)
        if state == 'finish':
            return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k3 - dest_sorted_gain * self._auto_finish_dest_sorted_bonus - ub_before_source * self._auto_finish_source_unlock_bonus + source_height * self._auto_finish_source_penalty + dest_height * self._auto_score_k5 + (self.problem.inst.H - dest_slack_after) * self._auto_finish_dest_fill_penalty - sim.sorted_n[action.sd] * self._auto_score_k2
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - sim.sorted_n[action.sd] * self._auto_score_k2 + dest_height * self._auto_score_k5 - source_height * self._auto_score_k5

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityFinishUnlockSortedBias(problem)
_MACHINE = RepairPriorityFinishUnlockSortedBias
_AUTO = {'score_k1': 80.0, 'score_k2': 20.0, 'score_k3': 15.0, 'score_k4': 3.0, 'score_k5': 0.5, 'finish_bad_threshold': 2, 'finish_source_penalty': 4.0, 'finish_dest_sorted_bonus': 14.0, 'finish_source_unlock_bonus': 10.0, 'finish_dest_fill_penalty': 2.5}

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
