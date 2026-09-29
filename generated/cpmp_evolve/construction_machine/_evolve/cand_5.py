COMPONENT = {'name': 'repair_priority_source_bad_dest_fit', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 90.0}, 'score_k2': {'type': 'float', 'range': [0.0, 120.0], 'default': 18.0}, 'score_k3': {'type': 'float', 'range': [0.0, 120.0], 'default': 14.0}, 'score_k4': {'type': 'float', 'range': [0.0, 60.0], 'default': 8.0}, 'score_k5': {'type': 'float', 'range': [0.0, 60.0], 'default': 2.0}, 'repair_source_bad_bonus': {'type': 'float', 'range': [0.0, 40.0], 'default': 10.0}, 'repair_dest_fit_bonus': {'type': 'float', 'range': [0.0, 40.0], 'default': 14.0}, 'repair_dest_room_bonus': {'type': 'float', 'range': [0.0, 20.0], 'default': 3.0}, 'repair_source_height_penalty': {'type': 'float', 'range': [0.0, 20.0], 'default': 1.0}, 'finish_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2}, 'finish_source_penalty': {'type': 'float', 'range': [0.0, 20.0], 'default': 4.0}}}
from core.machine import FALLBACK

class RepairPrioritySourceBadDestFit:
    _auto_score_k1 = 90.0
    _auto_score_k2 = 18.0
    _auto_score_k3 = 14.0
    _auto_score_k4 = 8.0
    _auto_score_k5 = 2.0
    _auto_repair_source_bad_bonus = 10.0
    _auto_repair_dest_fit_bonus = 14.0
    _auto_repair_dest_room_bonus = 3.0
    _auto_repair_dest_sorted_bonus = 8.0
    _auto_repair_source_height_penalty = 1.0
    _auto_finish_bad_threshold = 2
    _auto_finish_source_penalty = 4.0
    _auto_finish_dest_bonus = 12.0
    _auto_finish_ub_penalty = 18.0
    _auto_finish_height_penalty = 1.0
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
        c = partial.g(action.so)
        dest_fit = 1 if c <= partial.g(action.sd) else 0
        dest_room = partial.e(action.sd)
        dest_is_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_is_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - source_sorted_loss * self._auto_score_k5 - dest_prefix * self._auto_score_k2 + dest_height * self._auto_score_k5 - source_height * self._auto_repair_source_height_penalty - (partial.ub(action.so) > 0) * self._auto_repair_source_bad_bonus - dest_fit * self._auto_repair_dest_fit_bonus - dest_room * self._auto_repair_dest_room_bonus - dest_is_sorted_after * self._auto_repair_dest_sorted_bonus + dest_is_sorted_before * self._auto_score_k5

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairPrioritySourceBadDestFit(problem)
_MACHINE = RepairPrioritySourceBadDestFit
_AUTO = {'score_k1': 90.0, 'score_k2': 18.0, 'score_k3': 14.0, 'score_k4': 8.0, 'score_k5': 2.0, 'repair_source_bad_bonus': 10.0, 'repair_dest_fit_bonus': 14.0, 'repair_dest_room_bonus': 3.0, 'repair_dest_sorted_bonus': 8.0, 'repair_source_height_penalty': 1.0, 'finish_bad_threshold': 2, 'finish_source_penalty': 4.0, 'finish_dest_bonus': 12.0, 'finish_ub_penalty': 18.0, 'finish_height_penalty': 1.0}

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
