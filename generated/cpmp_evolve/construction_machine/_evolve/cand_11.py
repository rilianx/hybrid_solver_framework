COMPONENT = {'name': 'repair_priority_finish_unlock_dest_balance', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 80.0}, 'score_k2': {'type': 'float', 'range': [0.0, 80.0], 'default': 20.0}, 'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 15.0}, 'finish_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2}, 'finish_source_penalty': {'type': 'float', 'range': [0.0, 20.0], 'default': 4.0}, 'finish_unlock_bonus': {'type': 'float', 'range': [0.0, 40.0], 'default': 14.0}, 'finish_dest_fit_bonus': {'type': 'float', 'range': [0.0, 40.0], 'default': 10.0}}}
from core.machine import FALLBACK

class RepairPriorityFinishUnlockDestBalance:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 20.0
    _auto_score_k3 = 15.0
    _auto_finish_bad_threshold = 2
    _auto_finish_source_penalty = 4.0
    _auto_finish_unlock_bonus = 14.0
    _auto_finish_dest_fit_bonus = 10.0
    _auto_finish_dest_height_penalty = 1.0
    _auto_finish_source_ub_penalty = 6.0
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
        source_height = partial.h(action.so)
        dest_height_after = sim.h(action.sd)
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_unlock_before = partial.ub(action.sd)
        dest_unlock_after = sim.ub(action.sd)
        dest_unlock_gain = dest_unlock_after - dest_unlock_before
        dest_prefix_after = sim.sorted_n[action.sd]
        if state == 'finish':
            return bad_after * self._auto_score_k1 + ub_after_source * self._auto_finish_source_ub_penalty + source_height * self._auto_finish_source_penalty + dest_height_after * self._auto_finish_dest_height_penalty - dest_sorted_gain * self._auto_finish_dest_fit_bonus - dest_unlock_gain * self._auto_finish_unlock_bonus - dest_prefix_after * self._auto_score_k2 + ub_before_source * self._auto_score_k3
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k2 - dest_prefix_after * self._auto_score_k2 + dest_height_after * self._auto_score_k3 - source_height * self._auto_score_k3

    def update(self, partial, state, memory, action):
        return (partial.bad(),)
_MACHINE = RepairPriorityFinishUnlockDestBalance

def build_component(problem, **params):
    obj = _MACHINE(problem)
    for k, v in COMPONENT['params'].items():
        setattr(obj, '_auto_' + k, params.get(k, v['default']))
    return obj
