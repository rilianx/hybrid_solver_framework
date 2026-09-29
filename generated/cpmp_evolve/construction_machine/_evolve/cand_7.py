COMPONENT = {
    'name': 'repair_priority_promote_finish_state',
    'slot': 'construction_machine',
    'compatible_skeletons': ['CONSTRUCT'],
    'requires': [],
    'params': {
        'score_k1': {'type': 'float', 'range': [0.0, 200.0], 'default': 80.0},
        'score_k2': {'type': 'float', 'range': [0.0, 120.0], 'default': 25.0},
        'score_k3': {'type': 'float', 'range': [0.0, 80.0], 'default': 15.0},
        'score_k4': {'type': 'float', 'range': [0.0, 40.0], 'default': 8.0},
        'score_k5': {'type': 'float', 'range': [0.0, 20.0], 'default': 2.0},
        'score_k6': {'type': 'float', 'range': [0.0, 20.0], 'default': 1.0},
        'finish_bad_threshold': {'type': 'int', 'range': [0, 10], 'default': 2},
    },
}

from core.machine import FALLBACK


class RepairPriorityPromoteFinishState:
    _auto_score_k1 = 80.0
    _auto_score_k2 = 25.0
    _auto_score_k3 = 15.0
    _auto_score_k4 = 8.0
    _auto_score_k5 = 2.0
    _auto_score_k6 = 1.0
    _auto_finish_bad_threshold = 2

    states = ('repair', 'finish')

    def __init__(self, problem):
        self.problem = problem

    def _has_promising_sorted_dest(self, partial):
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            for sd in range(partial.S):
                if so == sd or len(partial.stacks[sd]) >= partial.H:
                    continue
                if partial.is_sorted_stack(sd) and c <= partial.g(sd):
                    return True
        return False

    def _finish_ready(self, partial):
        return partial.bad() <= self._auto_finish_bad_threshold or self._has_promising_sorted_dest(partial)

    def initial(self, partial):
        if self._finish_ready(partial):
            return ('finish', (partial.bad(),))
        return ('repair', (partial.bad(),))

    def transition(self, partial, state, memory):
        if partial.is_sorted() and partial.bad() <= self._auto_finish_bad_threshold:
            return (FALLBACK, ())
        if state == 'repair' and self._finish_ready(partial):
            return ('finish', memory)
        if state == 'finish' and not self._has_promising_sorted_dest(partial) and partial.bad() > self._auto_finish_bad_threshold:
            return ('repair', memory)
        return (state, memory)

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
            return (
                bad_after * self._auto_score_k1
                + ub_after_source * self._auto_score_k2
                - ub_before_source * self._auto_score_k3
                - dest_sorted_gain * self._auto_score_k4
                - dest_prefix * self._auto_score_k5
                - (1 if dest_sorted_after else 0) * self._auto_score_k6
                + dest_height * self._auto_score_k6
                - source_height * self._auto_score_k6
            )

        return (
            bad_after * self._auto_score_k1
            + ub_after_source * self._auto_score_k2
            - ub_before_source * self._auto_score_k3
            - dest_sorted_gain * self._auto_score_k4
            - dest_prefix * self._auto_score_k2
            + dest_height * self._auto_score_k5
            - source_height * self._auto_score_k5
        )

    def update(self, partial, state, memory, action):
        return (partial.bad(),)


def _build_component_llm(problem):
    return RepairPriorityPromoteFinishState(problem)


_MACHINE = RepairPriorityPromoteFinishState
_AUTO = {
    'score_k1': 80.0,
    'score_k2': 25.0,
    'score_k3': 15.0,
    'score_k4': 8.0,
    'score_k5': 2.0,
    'score_k6': 1.0,
    'finish_bad_threshold': 2,
}


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
