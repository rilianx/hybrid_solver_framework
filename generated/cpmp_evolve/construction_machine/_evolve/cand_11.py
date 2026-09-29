COMPONENT = {'name': 'repair_priority_transition_strict_hysteresis', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 90.0}, 'score_k2': {'type': 'float', 'range': [0.0, 120.0], 'default': 18.0}, 'score_k3': {'type': 'float', 'range': [0.0, 120.0], 'default': 14.0}, 'score_k4': {'type': 'float', 'range': [0.0, 60.0], 'default': 8.0}, 'score_k5': {'type': 'float', 'range': [0.0, 60.0], 'default': 2.0}, 'finish_ub_threshold': {'type': 'int', 'range': [0, 20], 'default': 4}, 'repair_bad_threshold': {'type': 'int', 'range': [0, 20], 'default': 3}, 'repair_sorted_stacks_threshold': {'type': 'int', 'range': [0, 20], 'default': 2}, 'finish_source_penalty': {'type': 'float', 'range': [0.0, 20.0], 'default': 4.0}, 'finish_ub_penalty': {'type': 'float', 'range': [0.0, 30.0], 'default': 18.0}}}
from core.machine import FALLBACK

class RepairPriorityTransitionStrictHysteresis:
    _auto_score_k1 = 90.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 14.0
    _auto_score_k4 = 8.0
    _auto_score_k5 = 2.0
    _auto_finish_bad_threshold = 2
    _auto_finish_ub_threshold = 4
    _auto_repair_bad_threshold = 3
    _auto_repair_sorted_stacks_threshold = 2
    _auto_finish_source_penalty = 4.0
    _auto_finish_dest_bonus = 12.0
    _auto_finish_ub_penalty = 18.0
    _auto_finish_height_penalty = 1.0
    _auto_transition_hysteresis = 1
    states = ('finish', 'repair')

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('repair', (partial.bad(), self._ub_total(partial)))

    def _ub_total(self, partial):
        total = 0
        for i in range(partial.S):
            total += partial.ub(i)
        return total

    def _sorted_stacks(self, partial):
        count = 0
        for i in range(partial.S):
            if partial.is_sorted_stack(i):
                count += 1
        return count

    def transition(self, partial, state, memory):
        bad = partial.bad()
        ub_total = self._ub_total(partial)
        sorted_stacks = self._sorted_stacks(partial)
        if partial.is_sorted():
            return (FALLBACK, ())
        finish_bad = self._auto_finish_bad_threshold
        finish_ub = self._auto_finish_ub_threshold
        repair_bad = self._auto_repair_bad_threshold
        repair_sorted = self._auto_repair_sorted_stacks_threshold
        hyst = self._auto_transition_hysteresis
        if state == 'repair':
            if bad <= repair_bad and ub_total <= finish_ub + hyst or (sorted_stacks >= repair_sorted and bad <= 2 * repair_bad and (ub_total <= finish_ub)):
                return ('finish', (bad, ub_total))
            return ('repair', (bad, ub_total))
        if state == 'finish':
            prev_bad, prev_ub = memory if memory else (bad, ub_total)
            if bad <= finish_bad + hyst and ub_total <= finish_ub + hyst:
                return ('finish', (bad, ub_total))
            if bad <= prev_bad + hyst and ub_total <= prev_ub + hyst and (bad <= repair_bad):
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
        return (partial.bad(), self._ub_total(partial))
_MACHINE = RepairPriorityTransitionStrictHysteresis
_AUTO = {'score_k1': 90.0, 'score_k2': 18.0, 'score_k3': 14.0, 'score_k4': 8.0, 'score_k5': 2.0, 'finish_bad_threshold': 2, 'finish_ub_threshold': 4, 'repair_bad_threshold': 3, 'repair_sorted_stacks_threshold': 2, 'finish_source_penalty': 4.0, 'finish_dest_bonus': 12.0, 'finish_ub_penalty': 18.0, 'finish_height_penalty': 1.0, 'transition_hysteresis': 1}

def _build_component_llm(problem, **params):
    return RepairPriorityTransitionStrictHysteresis(problem)

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
