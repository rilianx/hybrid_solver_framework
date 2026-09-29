COMPONENT = {'name': 'safe_unlock_to_sorted_stack_focus_refine_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'bad_weight': {'type': 'float', 'range': [1.0, 10000.0], 'default': 1000.0}, 'ub_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 20.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 5.0}, 'source_sorted_penalty': {'type': 'float', 'range': [0.0, 100.0], 'default': 2.0}, 'dest_sorted_bonus': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStack:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_score_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, bad_weight: float=1000.0, ub_weight: float=20.0, dest_free_weight: float=5.0, source_sorted_penalty: float=2.0, dest_sorted_bonus: float=1.0):
        self._bad_weight = bad_weight
        self._ub_weight = ub_weight
        self._dest_free_weight = dest_free_weight
        self._source_sorted_penalty = source_sorted_penalty
        self._dest_sorted_bonus = dest_sorted_bonus

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        return memory

    def done(self, partial, memory):
        return partial.is_sorted()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        allowed = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            if not partial.valid(so, sd):
                continue
            allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        resulting_ub = 0
        for i in range(nxt.S):
            resulting_ub += nxt.ub(i)
        dest_free = partial.e(sd)
        source_sorted = 1.0 if partial.is_sorted_stack(so) else 0.0
        dest_sorted = 1.0 if partial.is_sorted_stack(sd) else 0.0
        score = resulting_bad * self._bad_weight + resulting_ub * self._ub_weight + dest_free * self._dest_free_weight + source_sorted * self._source_sorted_penalty - dest_sorted * self._dest_sorted_bonus
        return float(score)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeUnlockToSortedStack(**params)])
_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 10.0, 'safe_unlock_to_sorted_stack_score_k2': 0.01}
_AUTO_OWNER = {'safe_unlock_to_sorted_stack_score_k1': 'SafeUnlockToSortedStack', 'safe_unlock_to_sorted_stack_score_k2': 'SafeUnlockToSortedStack'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeUnlockToSortedStack': SafeUnlockToSortedStack}
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
