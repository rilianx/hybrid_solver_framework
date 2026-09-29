COMPONENT = {'name': 'finish_priority_sorted_gain', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'finish_source_sorted_loss_weight': {'type': 'float', 'range': [0.0, 120.0], 'default': 18.0}, 'finish_dest_height_weight': {'type': 'float', 'range': [0.0, 60.0], 'default': 3.0}, 'finish_source_height_weight': {'type': 'float', 'range': [0.0, 60.0], 'default': 4.0}, 'finish_dest_prefix_weight': {'type': 'float', 'range': [0.0, 60.0], 'default': 10.0}, 'finish_source_prefix_weight': {'type': 'float', 'range': [0.0, 60.0], 'default': 4.0}}}
from core.machine import FALLBACK

class FinishPrioritySortedGain:
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
    _auto_finish_gain_weight = 160.0
    _auto_finish_bad_weight = 120.0
    _auto_finish_ub_weight = 24.0
    _auto_finish_source_sorted_loss_weight = 18.0
    _auto_finish_dest_sorted_gain_weight = 22.0
    _auto_finish_dest_height_weight = 3.0
    _auto_finish_source_height_weight = 4.0
    _auto_finish_dest_prefix_weight = 10.0
    _auto_finish_source_prefix_weight = 4.0
    states = ('finish', 'repair')

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('repair', (partial.bad(), partial.bad()))

    def transition(self, partial, state, memory):
        bad = partial.bad()
        if partial.is_sorted():
            return (FALLBACK, ())
        ub_total = 0
        sorted_stacks = 0
        for i in range(partial.S):
            ub_total += partial.ub(i)
            if partial.is_sorted_stack(i):
                sorted_stacks += 1
        if state == 'repair':
            if bad <= self._auto_repair_bad_threshold:
                return ('finish', (bad, ub_total))
            if ub_total <= self._auto_finish_ub_threshold:
                return ('finish', (bad, ub_total))
            if sorted_stacks >= self._auto_repair_sorted_stacks_threshold and bad <= 2 * self._auto_repair_bad_threshold:
                return ('finish', (bad, ub_total))
            return ('repair', (bad, ub_total))
        if state == 'finish':
            if bad <= self._auto_finish_bad_threshold:
                return ('finish', (bad, ub_total))
            if ub_total <= self._auto_finish_ub_threshold:
                return ('finish', (bad, ub_total))
            if sorted_stacks >= self._auto_repair_sorted_stacks_threshold and bad <= 2 * self._auto_finish_bad_threshold:
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
            total_sorted_gain = sum(sim.sorted_n) - sum(partial.sorted_n)
            return bad_after * self._auto_finish_bad_weight + ub_after_source * self._auto_finish_ub_weight + source_sorted_loss * self._auto_finish_source_sorted_loss_weight - dest_sorted_gain * self._auto_finish_dest_sorted_gain_weight + source_height * self._auto_finish_source_height_weight + dest_height * self._auto_finish_dest_height_weight - dest_prefix * self._auto_finish_dest_prefix_weight - source_prefix * self._auto_finish_source_prefix_weight - total_sorted_gain * self._auto_finish_gain_weight + ub_before_source * self._auto_score_k3
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - source_sorted_loss * self._auto_score_k5 - dest_prefix * self._auto_score_k2 + dest_height * self._auto_score_k5 - source_height * self._auto_score_k5

    def update(self, partial, state, memory, action):
        return (partial.bad(), partial.bad())
_MACHINE = FinishPrioritySortedGain
_AUTO = {'score_k1': 90.0, 'score_k2': 18.0, 'score_k3': 14.0, 'score_k4': 8.0, 'score_k5': 2.0, 'finish_bad_threshold': 2, 'finish_ub_threshold': 4, 'repair_bad_threshold': 3, 'repair_sorted_stacks_threshold': 2, 'finish_source_penalty': 4.0, 'finish_dest_bonus': 12.0, 'finish_ub_penalty': 18.0, 'finish_height_penalty': 1.0, 'finish_gain_weight': 160.0, 'finish_bad_weight': 120.0, 'finish_ub_weight': 24.0, 'finish_source_sorted_loss_weight': 18.0, 'finish_dest_sorted_gain_weight': 22.0, 'finish_dest_height_weight': 3.0, 'finish_source_height_weight': 4.0, 'finish_dest_prefix_weight': 10.0, 'finish_source_prefix_weight': 4.0}

def _build_component_llm(problem, **params):
    return FinishPrioritySortedGain(problem)

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
