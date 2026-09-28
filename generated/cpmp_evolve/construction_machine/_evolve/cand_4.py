COMPONENT = {'name': 'repair_priority_unlock_and_finish_transition_hysteresis', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k4': {'type': 'float', 'range': [0.0, 50.0], 'default': 2.0}, 'score_k5': {'type': 'float', 'range': [0.0, 50.0], 'default': 1.0}, 'score_k6': {'type': 'float', 'range': [0.0, 0.2], 'default': 0.1}, 'score_k7': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}, 'finish_enter_bad_threshold': {'type': 'int', 'range': [0, 20], 'default': 4}, 'finish_enter_sorted_threshold': {'type': 'int', 'range': [0, 10], 'default': 1}, 'score_k10': {'type': 'float', 'range': [0.0, 1.0], 'default': 0.5}}}
from core.machine import FALLBACK

class RepairPriorityUnlockAndFinishTransitionHysteresis:
    _auto_score_k8 = 0.5
    _auto_score_k9 = 0.25
    _auto_score_k10 = 0.5
    _auto_score_k11 = 0.25
    _auto_score_k12 = 0.5
    _auto_score_k1 = 120.0
    _auto_score_k2 = 35.0
    _auto_score_k3 = 20.0
    _auto_score_k4 = 2.0
    _auto_score_k5 = 1.0
    _auto_score_k6 = 0.1
    _auto_score_k7 = 0.01
    _auto_finish_enter_bad_threshold = 4
    _auto_finish_enter_sorted_threshold = 1
    _auto_finish_exit_bad_threshold = 5
    _auto_finish_exit_sorted_threshold = 2
    _auto_finish_bias = 8.0
    states = ('repair', 'finish')

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        if partial.is_sorted():
            return (FALLBACK, ())
        bad = partial.bad()
        unsorted_stacks = sum((1 for i in range(partial.S) if not partial.is_sorted_stack(i)))
        if bad <= self._auto_finish_enter_bad_threshold and unsorted_stacks <= self._auto_finish_enter_sorted_threshold:
            return ('finish', (bad,))
        return ('repair', (bad,))

    def transition(self, partial, state, memory):
        if partial.is_sorted():
            return (FALLBACK, ())
        bad = partial.bad()
        unsorted_stacks = sum((1 for i in range(partial.S) if not partial.is_sorted_stack(i)))
        enter_finish = bad <= self._auto_finish_enter_bad_threshold and unsorted_stacks <= self._auto_finish_enter_sorted_threshold
        exit_finish = bad > self._auto_finish_exit_bad_threshold or unsorted_stacks > self._auto_finish_exit_sorted_threshold
        if state == 'repair':
            if enter_finish:
                return ('finish', (bad,))
            return ('repair', memory)
        if state == 'finish':
            if exit_finish and (not enter_finish):
                return ('repair', (bad,))
            return ('finish', memory)
        return (FALLBACK, ())

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
        source_height = sim.h(action.so)
        dest_height = sim.h(action.sd)
        if state == 'repair':
            return bad_after * self._auto_score_k1 + ub_after * self._auto_score_k2 - ub_source * self._auto_score_k3 + source_sorted * self._auto_score_k4 + (1 - dest_sorted_after) * self._auto_score_k5 + (dest_sorted_before - dest_sorted_after) * self._auto_score_k4 - fit_gain * self._auto_score_k3 + dest_height * self._auto_score_k6 + source_height * self._auto_score_k7
        move_penalty = 0.0
        if partial.is_sorted_stack(action.so):
            move_penalty += self._auto_finish_bias
        if not partial.is_sorted_stack(action.sd):
            move_penalty += self._auto_finish_bias * self._auto_score_k8
        return bad_after * (self._auto_score_k1 + self._auto_finish_bias) + ub_after * (self._auto_score_k2 + self._auto_finish_bias * self._auto_score_k9) - fit_gain * (self._auto_score_k3 + self._auto_finish_bias) - ub_source * (self._auto_score_k3 * self._auto_score_k10) + (1 - dest_sorted_after) * (self._auto_score_k5 + self._auto_finish_bias * self._auto_score_k11) + (dest_sorted_before - dest_sorted_after) * (self._auto_score_k4 + self._auto_finish_bias * self._auto_score_k12) + dest_height * self._auto_score_k6 + source_height * self._auto_score_k7 + move_penalty

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPriorityUnlockAndFinishTransitionHysteresis(problem)
_MACHINE = RepairPriorityUnlockAndFinishTransitionHysteresis
_AUTO = {'score_k1': 120.0, 'score_k2': 35.0, 'score_k3': 20.0, 'score_k4': 2.0, 'score_k5': 1.0, 'score_k6': 0.1, 'score_k7': 0.01, 'finish_enter_bad_threshold': 4, 'finish_enter_sorted_threshold': 1, 'finish_exit_bad_threshold': 5, 'finish_exit_sorted_threshold': 2, 'finish_bias': 8.0, 'score_k8': 0.5, 'score_k9': 0.25, 'score_k10': 0.5, 'score_k11': 0.25, 'score_k12': 0.5}

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
