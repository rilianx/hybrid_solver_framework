COMPONENT = {'name': 'promote_into_sorted_stack', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'promote_threshold': {'type': 'int', 'range': [0, 2], 'default': 0}, 'score_k1': {'type': 'int', 'range': [0, 20], 'default': 10}}}
from core.machine import FALLBACK

class PromoteIntoSortedStack:
    _auto_score_k1 = 10
    'Estado único que prioriza mover contenedores a una pila ya ordenada o que quede ordenada.'
    states = ('promote',)

    def __init__(self, problem, promote_bonus: float=1.0, promote_threshold: int=0):
        self.problem = problem
        self._auto_promote_bonus = promote_bonus
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
        sim = partial.copy(track=False)
        sim.move(so, sd)
        after_bad = sim.bad()
        after_ub = sim.ub(so) + sim.ub(sd)
        after_sorted = 1 if sim.is_sorted_stack(sd) else 0
        gain = before_bad - after_bad + (after_ub - before_ub)
        promote_gain = after_sorted - before_sorted
        return float(after_bad * 1000 + after_ub * self._auto_score_k1 - promote_gain * self._auto_promote_bonus - gain)

    def update(self, partial, state, memory, action):
        return memory

def _build_component_llm(problem, **params):
    promote_bonus = params.get('promote_bonus', 1.0)
    promote_threshold = params.get('promote_threshold', 0)
    return PromoteIntoSortedStack(problem, promote_bonus=promote_bonus, promote_threshold=promote_threshold)
_MACHINE = PromoteIntoSortedStack
_AUTO = {'score_k1': 10}

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT); se fijan en la clase mientras se construye (por si
    `__init__` los usa) y en la instancia."""
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
