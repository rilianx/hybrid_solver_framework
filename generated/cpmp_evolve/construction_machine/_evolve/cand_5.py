COMPONENT = {'name': 'safe_unlock_to_sorted_stack_refined_rule_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 2000.0], 'default': 1000.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 200.0], 'default': 10.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 200.0], 'default': 1.0}, 'prefer_unlock_bonus': {'type': 'float', 'range': [0.0, 100.0], 'default': 12.0}, 'safe_unlock_to_sorted_stack_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStack:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_score_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, safe_dest_bonus: float=14.0, source_sorted_bonus: float=10.0, source_bad_weight: float=1000.0, dest_free_weight: float=10.0, dest_top_weight: float=1.0, created_bad_weight: float=250.0, prefer_empty_dest_bonus: float=6.0, prefer_unlock_bonus: float=12.0):
        self._safe_dest_bonus = safe_dest_bonus
        self._source_sorted_bonus = source_sorted_bonus
        self._source_bad_weight = source_bad_weight
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._created_bad_weight = created_bad_weight
        self._prefer_empty_dest_bonus = prefer_empty_dest_bonus
        self._prefer_unlock_bonus = prefer_unlock_bonus

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        good = []
        unlock = []
        fallback = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            if not partial.stacks[so]:
                continue
            if len(partial.stacks[sd]) >= partial.H:
                continue
            c = partial.stacks[so][-1]
            src_sorted = partial.sorted_n[so] == len(partial.stacks[so])
            dest_sorted = partial.sorted_n[sd] == len(partial.stacks[sd])
            dest_empty = len(partial.stacks[sd]) == 0
            safe_dest = dest_sorted and c <= partial.g(sd)
            if safe_dest:
                good.append(action)
                continue
            if not src_sorted:
                if dest_empty or c >= partial.g(sd):
                    unlock.append(action)
                    continue
            if dest_empty or dest_sorted:
                fallback.append(action)
        return good + unlock + fallback

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        c = partial.stacks[so][-1]
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        created_bad = max(0, resulting_bad - partial.bad())
        dest_is_safe = 1.0 if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd) else 0.0
        source_is_sorted = 1.0 if partial.sorted_n[so] == len(partial.stacks[so]) else 0.0
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        dest_empty = 1.0 if len(partial.stacks[sd]) == 0 else 0.0
        unlocks_source = 1.0 if partial.sorted_n[so] < len(partial.stacks[so]) else 0.0
        score = resulting_bad * self._source_bad_weight + created_bad * self._created_bad_weight - dest_is_safe * self._safe_dest_bonus - source_is_sorted * self._source_sorted_bonus - dest_empty * self._prefer_empty_dest_bonus - unlocks_source * self._prefer_unlock_bonus + source_bad * self._auto_safe_unlock_to_sorted_stack_score_k1 + dest_free * self._dest_free_weight + dest_top * self._dest_top_weight - c * self._auto_safe_unlock_to_sorted_stack_score_k2
        return float(score)

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
