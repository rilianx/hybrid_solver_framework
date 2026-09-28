COMPONENT = {'name': 'repair_priority_promote_sorted_dest_finish_state', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 80.0}, 'score_k2': {'type': 'float', 'range': [0.0, 80.0], 'default': 20.0}, 'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 15.0}, 'finish_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2}, 'finish_bad_weight': {'type': 'float', 'range': [0.0, 200.0], 'default': 120.0}, 'finish_ub_weight': {'type': 'float', 'range': [0.0, 80.0], 'default': 25.0}, 'finish_dest_prefix_weight': {'type': 'float', 'range': [0.0, 80.0], 'default': 20.0}}}
from core.machine import FALLBACK

class RepairPriorityPromoteSortedDestFinishState:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 20.0
    _auto_score_k3 = 15.0
    _auto_score_k4 = 3.0
    _auto_score_k5 = 0.5
    _auto_finish_bad_threshold = 2
    _auto_finish_bad_weight = 120.0
    _auto_finish_ub_weight = 25.0
    _auto_finish_sorted_gain_weight = 6.0
    _auto_finish_dest_prefix_weight = 20.0
    _auto_finish_dest_height_weight = 0.5
    _auto_finish_source_height_weight = 0.5
    states = ('repair', 'finish')

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return ('finish', (partial.bad(),))

    def transition(self, partial, state, memory):
        bad = partial.bad()
        if state == 'finish':
            if not partial.is_sorted() and bad > 0:
                return ('repair', (bad,))
            if bad > self._auto_finish_bad_threshold:
                return ('repair', (bad,))
            return ('finish', memory)
        if state == 'repair':
            if partial.is_sorted() and bad <= self._auto_finish_bad_threshold:
                return ('finish', (bad,))
            if bad <= self._auto_finish_bad_threshold:
                return ('finish', (bad,))
            return ('repair', memory)
        return (state, memory)

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        sim.move(action.so, action.sd)
        bad_after = sim.bad()
        ub_after_source = sim.ub(action.so)
        ub_before_source = partial.ub(action.so)
        dest_sorted_before = 1 if partial.is_sorted_stack(action.sd) else 0
        dest_sorted_after = 1 if sim.is_sorted_stack(action.sd) else 0
        dest_sorted_gain = dest_sorted_after - dest_sorted_before
        dest_prefix = sim.sorted_n[action.sd]
        source_height = partial.h(action.so)
        dest_height = sim.h(action.sd)
        if state == 'finish':
            return bad_after * self._auto_finish_bad_weight + ub_after_source * self._auto_finish_ub_weight - dest_sorted_gain * self._auto_finish_sorted_gain_weight - dest_prefix * self._auto_finish_dest_prefix_weight + dest_height * self._auto_finish_dest_height_weight - source_height * self._auto_finish_source_height_weight
        return bad_after * self._auto_score_k1 + ub_after_source * self._auto_score_k2 - ub_before_source * self._auto_score_k3 - dest_sorted_gain * self._auto_score_k4 - dest_prefix * self._auto_score_k2 + dest_height * self._auto_score_k5 - source_height * self._auto_score_k5

    def update(self, partial, state, memory, action):
        return (partial.bad(),)
_MACHINE = RepairPriorityPromoteSortedDestFinishState
_AUTO = {'score_k1': 80.0, 'score_k2': 20.0, 'score_k3': 15.0, 'score_k4': 3.0, 'score_k5': 0.5, 'finish_bad_threshold': 2, 'finish_bad_weight': 120.0, 'finish_ub_weight': 25.0, 'finish_sorted_gain_weight': 6.0, 'finish_dest_prefix_weight': 20.0, 'finish_dest_height_weight': 0.5, 'finish_source_height_weight': 0.5}

def build_component(problem, **params):
    obj = _MACHINE(problem)
    for k, v in {**_AUTO, **params}.items():
        setattr(obj, '_auto_' + k, v)
    return obj
