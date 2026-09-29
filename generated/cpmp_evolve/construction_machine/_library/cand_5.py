COMPONENT = {'name': 'safe_relocate_sorted_support_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'bad_weight': {'type': 'float', 'range': [100000.0, 5000000.0], 'default': 1000000.0}}}
from core.rules import RuleMachine

class SafeRelocateGreedy:
    _auto_safe_relocate_greedy_score_k1 = 5.0
    'Regla simple: prioriza recolocaciones seguras hacia pilas ya ordenadas.'
    name = 'safe_relocate_greedy'
    priority = 100

    def __init__(self, bad_weight: float=1000000.0, ub_weight: float=10000.0, source_bad_weight: float=100.0, source_sorted_penalty: float=10.0, dest_sorted_bonus: float=1.0, move_index_weight: float=0.0001):
        self.bad_weight = float(bad_weight)
        self.ub_weight = float(ub_weight)
        self.source_bad_weight = float(source_bad_weight)
        self.source_sorted_penalty = float(source_sorted_penalty)
        self.dest_sorted_bonus = float(dest_sorted_bonus)
        self.move_index_weight = float(move_index_weight)

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        candidates = list(candidates)
        if not candidates:
            return []
        safe_sorted = []
        safe_any = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            c = partial.g(so)
            dest_keeps_sorted = partial.is_sorted_stack(sd) and (partial.h(sd) == 0 or c <= partial.g(sd))
            if dest_keeps_sorted:
                safe_sorted.append(action)
            if partial.h(sd) == 0 or c <= partial.g(sd):
                safe_any.append(action)
        if safe_sorted:
            return safe_sorted
        if safe_any:
            return safe_any
        return candidates

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy(track=False)
        nxt.move(so, sd)
        new_bad = float(nxt.bad())
        new_ub = float(sum((nxt.ub(i) for i in range(nxt.S))))
        source_bad = float(partial.h(so) - partial.sorted_n[so])
        source_sorted = 1.0 if partial.is_sorted_stack(so) else 0.0
        dest_sorted = 1.0 if partial.is_sorted_stack(sd) else 0.0
        dest_keeps_sorted = 1.0 if partial.is_sorted_stack(sd) and (partial.h(sd) == 0 or partial.g(so) <= partial.g(sd)) else 0.0
        score = 0.0
        score += self.bad_weight * new_bad
        score += self.ub_weight * new_ub
        score += self.source_bad_weight * source_bad
        score += self.source_sorted_penalty * source_sorted
        score -= self.dest_sorted_bonus * dest_sorted
        score -= self._auto_safe_relocate_greedy_score_k1 * dest_keeps_sorted
        score += self.move_index_weight * float(so * partial.S + sd)
        return score

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeRelocateGreedy(**params)])
_AUTO = {'safe_relocate_greedy_score_k1': 5.0}
_AUTO_OWNER = {'safe_relocate_greedy_score_k1': 'SafeRelocateGreedy'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeRelocateGreedy': SafeRelocateGreedy}
_AUTO_FACTORY = '_build_component_llm'

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT; `_AUTO_OWNER`: la clase de cada uno). Se fijan en las clases
    mientras se construye (por si un `__init__` los usa) y en cada instancia: la máquina, sus
    reglas y sus transiciones."""
    attrs = globals().get('_AUTO_ATTR', {})
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    lifted = [k for k in auto if k not in attrs]
    saved = {k: getattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k) for k in lifted}
    for k in lifted:
        setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k, auto[k])
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k, v)
    parts = [obj, getattr(obj, 'transitions', None), *list(getattr(obj, 'rules', None) or [])]
    for part in parts:
        for k, v in auto.items():
            if part is not None and isinstance(part, _AUTO_CLASSES[_AUTO_OWNER[k]]):
                setattr(part, attrs.get(k, '_auto_' + k), v)
    return obj
