COMPONENT = {'name': 'promote_priority_sorted_destination', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'promote_threshold': {'type': 'int', 'range': [0, 2], 'default': 0}, 'score_k_ub': {'type': 'int', 'range': [0, 50], 'default': 10}, 'score_k_dest_top': {'type': 'int', 'range': [0, 50], 'default': 3}}}
from core.machine import FALLBACK

class PromotePrioritySortedDestination:
    _auto_score_k_bad = 1000
    _auto_score_k_ub = 10
    _auto_score_k_sorted = 25
    _auto_score_k_source_ub = 5
    _auto_score_k_dest_top = 3
    states = ('promote',)

    def __init__(self, problem, promote_threshold: int=0):
        self.problem = problem
        self._auto_promote_threshold = promote_threshold

    def initial(self, partial):
        return ('promote', ())

    def transition(self, partial, state, memory):
        if state != 'promote':
            return (FALLBACK, ())
        best_gain = 0
        has_promising = False
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                if c <= partial.g(sd):
                    gain = 1 if partial.is_sorted_stack(sd) else 0
                    if gain >= self._auto_promote_threshold:
                        has_promising = True
                        if gain > best_gain:
                            best_gain = gain
        return ('promote', ()) if has_promising else (FALLBACK, ())

    def score(self, partial, state, memory, action):
        if state != 'promote':
            return 0.0
        so, sd = (action.so, action.sd)
        before_bad = partial.bad()
        before_ub = partial.ub(so) + partial.ub(sd)
        before_sorted = 1 if partial.is_sorted_stack(sd) else 0
        source_ub = partial.ub(so)
        dest_top = partial.g(sd)
        sim = partial.copy(track=False)
        sim.move(so, sd)
        after_bad = sim.bad()
        after_ub = sim.ub(so) + sim.ub(sd)
        after_sorted = 1 if sim.is_sorted_stack(sd) else 0
        gain_bad = before_bad - after_bad
        gain_ub = before_ub - after_ub
        promote_gain = after_sorted - before_sorted
        return float(after_bad * self._auto_score_k_bad + after_ub * self._auto_score_k_ub - promote_gain * self._auto_score_k_sorted - gain_bad - gain_ub + source_ub * self._auto_score_k_source_ub - dest_top * self._auto_score_k_dest_top)

    def update(self, partial, state, memory, action):
        return memory

def _build_component_llm(problem, **params):
    promote_threshold = params.get('promote_threshold', 0)
    return PromotePrioritySortedDestination(problem, promote_threshold=promote_threshold)
_MACHINE = PromotePrioritySortedDestination
_AUTO = {'score_k_bad': 1000, 'score_k_ub': 10, 'score_k_sorted': 25, 'score_k_source_ub': 5, 'score_k_dest_top': 3}

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos
    (`_AUTO`, declarados en COMPONENT) se fijan en la clase mientras se construye y en la instancia."""
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
