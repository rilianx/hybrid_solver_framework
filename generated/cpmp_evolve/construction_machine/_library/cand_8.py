COMPONENT = {'name': 'safe_relocate_greedy_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_relocate_greedy_score_k1': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.rules import RuleMachine

class SafeRelocateGreedy:
    _auto_safe_relocate_greedy_score_k1 = 0.01
    _auto_safe_relocate_greedy_score_k2 = 0.001
    name = 'safe_relocate_greedy'
    priority = 100

    def __init__(self, prefer_sorted_support: float=12.0, prefer_bad_top_moves: float=8.0, penalize_source_sorted: float=6.0):
        self.prefer_sorted_support = float(prefer_sorted_support)
        self.prefer_bad_top_moves = float(prefer_bad_top_moves)
        self.penalize_source_sorted = float(penalize_source_sorted)

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        chosen = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            top = partial.g(so)
            source_bad_top = partial.h(so) > partial.sorted_n[so]
            dest_sorted_and_safe = partial.is_sorted_stack(sd) and top <= partial.g(sd)
            if source_bad_top or dest_sorted_and_safe:
                chosen.append(action)
        return chosen

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy(track=False)
        nxt.move(so, sd)
        source_bad_top = partial.h(so) > partial.sorted_n[so]
        dest_sorted_and_safe = partial.is_sorted_stack(sd) and partial.g(so) <= partial.g(sd)
        source_sorted = partial.is_sorted_stack(so)
        score = 1000000.0 * float(nxt.bad())
        score += 10000.0 * float(nxt.ub(so))
        score += 1000.0 * float(nxt.ub(sd))
        if dest_sorted_and_safe:
            score -= self.prefer_sorted_support
        if source_bad_top:
            score -= self.prefer_bad_top_moves
        if source_sorted:
            score += self.penalize_source_sorted
        score += self._auto_safe_relocate_greedy_score_k1 * float(nxt.h(sd))
        score += self._auto_safe_relocate_greedy_score_k2 * float(nxt.h(so))
        score += 0.0001 * float(so)
        score += 1e-05 * float(sd)
        return score

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeRelocateGreedy(prefer_sorted_support=params.get('prefer_sorted_support', 12.0), prefer_bad_top_moves=params.get('prefer_bad_top_moves', 8.0), penalize_source_sorted=params.get('penalize_source_sorted', 6.0))])
_AUTO = {'safe_relocate_greedy_score_k1': 0.01, 'safe_relocate_greedy_score_k2': 0.001}
_AUTO_OWNER = {'safe_relocate_greedy_score_k1': 'SafeRelocateGreedy', 'safe_relocate_greedy_score_k2': 'SafeRelocateGreedy'}
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
