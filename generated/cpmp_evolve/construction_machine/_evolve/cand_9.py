COMPONENT = {'name': 'repair_priority_transition_safe_hysteresis', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'finish_enter_ub_threshold': {'type': 'int', 'range': [0, 20], 'default': 4}, 'finish_exit_bad_threshold': {'type': 'int', 'range': [0, 20], 'default': 5}, 'finish_exit_ub_threshold': {'type': 'int', 'range': [0, 20], 'default': 7}, 'repair_enter_ub_threshold': {'type': 'int', 'range': [0, 20], 'default': 5}, 'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 90.0}, 'score_k2': {'type': 'float', 'range': [0.0, 200.0], 'default': 18.0}, 'score_k3': {'type': 'float', 'range': [0.0, 200.0], 'default': 14.0}, 'score_k4': {'type': 'float', 'range': [0.0, 200.0], 'default': 8.0}, 'score_k5': {'type': 'float', 'range': [0.0, 200.0], 'default': 2.0}, 'finish_ub_penalty': {'type': 'float', 'range': [0.0, 200.0], 'default': 12.0}, 'finish_source_penalty': {'type': 'float', 'range': [0.0, 200.0], 'default': 6.0}, 'finish_height_penalty': {'type': 'float', 'range': [0.0, 200.0], 'default': 4.0}}}
from core.machine import FALLBACK

class RepairPriorityTransitionSafeHysteresis:
    _auto_finish_enter_bad_threshold = 2
    _auto_finish_enter_ub_threshold = 4
    _auto_finish_exit_bad_threshold = 5
    _auto_finish_exit_ub_threshold = 7
    _auto_repair_enter_bad_threshold = 3
    _auto_repair_enter_ub_threshold = 5
    _auto_sorted_stacks_threshold = 2
    _auto_score_k1 = 90.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 14.0
    _auto_score_k4 = 8.0
    _auto_score_k5 = 2.0
    _auto_finish_ub_penalty = 12.0
    _auto_finish_source_penalty = 6.0
    _auto_finish_height_penalty = 4.0
    _auto_finish_dest_bonus = 5.0
    states = ('finish', 'repair')

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('repair', (partial.bad(), sum((partial.ub(i) for i in range(partial.S)))))

    def _summary(self, partial):
        bad = partial.bad()
        ub_total = 0
        sorted_stacks = 0
        for i in range(partial.S):
            ub_total += partial.ub(i)
            if partial.is_sorted_stack(i):
                sorted_stacks += 1
        return (bad, ub_total, sorted_stacks)

    def transition(self, partial, state, memory):
        bad, ub_total, sorted_stacks = self._summary(partial)
        if partial.is_sorted():
            return (FALLBACK, ())
        if state == 'repair':
            if bad <= self._auto_repair_enter_bad_threshold or ub_total <= self._auto_repair_enter_ub_threshold or (sorted_stacks >= self._auto_sorted_stacks_threshold and bad <= 2 * self._auto_repair_enter_bad_threshold):
                return ('finish', (bad, ub_total))
            return ('repair', (bad, ub_total))
        if state == 'finish':
            if bad > self._auto_finish_exit_bad_threshold or ub_total > self._auto_finish_exit_ub_threshold:
                return ('repair', (bad, ub_total))
            if bad <= self._auto_finish_enter_bad_threshold or ub_total <= self._auto_finish_enter_ub_threshold or (sorted_stacks >= self._auto_sorted_stacks_threshold and bad <= 2 * self._auto_finish_enter_bad_threshold):
                return ('finish', (bad, ub_total))
            return ('repair', (bad, ub_total))
        return (FALLBACK, ())

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        sim.move(action.so, action.sd)
        bad_after = sim.bad()
        ub_after_source = sim.ub(action.so)
        ub_before_source = partial.ub(action.so)
        source_height = partial.h(action.so)
        dest_height = sim.h(action.sd)
        source_sorted_before = 1 if partial.is_sorted_stack(action.so) else 0
        source_sorted_after = 1 if sim.is_sorted_stack(action.so) else 0
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        source_sorted_loss = source_sorted_before - source_sorted_after
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix = sim.sorted_n[action.sd]
        source_prefix = sim.sorted_n[action.so]
        if state == 'finish':
            return bad_after * self._auto_score_k1 + ub_after_source * self._auto_finish_ub_penalty + ub_before_source * self._auto_score_k3 + source_height * self._auto_finish_source_penalty + dest_height * self._auto_finish_height_penalty - dest_sorted_gain * self._auto_finish_dest_bonus - source_sorted_loss * self._auto_score_k4 - dest_prefix * self._auto_score_k2 - source_prefix * self._auto_score_k5
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - source_sorted_loss * self._auto_score_k5 - dest_prefix * self._auto_score_k2 + dest_height * self._auto_score_k5 - source_height * self._auto_score_k5

    def update(self, partial, state, memory, action):
        return (partial.bad(), sum((partial.ub(i) for i in range(partial.S))))

def build_component(problem, **params):
    obj = RepairPriorityTransitionSafeHysteresis(problem)
    for key, spec in COMPONENT['params'].items():
        value = params.get(key, spec['default'])
        setattr(obj, '_auto_' + key, value)
    return obj
