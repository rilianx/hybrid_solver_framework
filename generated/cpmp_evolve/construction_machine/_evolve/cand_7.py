COMPONENT = {'name': 'safe_unlock_to_sorted_stack_refined_rule_v4', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 2000.0], 'default': 1000.0}, 'dest_safe_bonus': {'type': 'float', 'range': [0.0, 50.0], 'default': 15.0}, 'dest_sorted_bonus': {'type': 'float', 'range': [0.0, 50.0], 'default': 10.0}, 'source_sorted_penalty': {'type': 'float', 'range': [0.0, 50.0], 'default': 12.0}, 'source_unlock_bonus': {'type': 'float', 'range': [0.0, 50.0], 'default': 8.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 8.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'dest_headroom_weight': {'type': 'float', 'range': [0.0, 50.0], 'default': 2.0}, 'c_top_weight': {'type': 'float', 'range': [0.0, 20.0], 'default': 0.01}, 'safe_unlock_to_sorted_stack_score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStackRefinedRuleV4:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_score_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, source_bad_weight: float=1000.0, created_bad_weight: float=200.0, dest_safe_bonus: float=15.0, dest_sorted_bonus: float=10.0, source_sorted_penalty: float=12.0, source_unlock_bonus: float=8.0, dest_free_weight: float=8.0, dest_top_weight: float=1.0, dest_headroom_weight: float=2.0, c_top_weight: float=0.01):
        self._source_bad_weight = source_bad_weight
        self._created_bad_weight = created_bad_weight
        self._dest_safe_bonus = dest_safe_bonus
        self._dest_sorted_bonus = dest_sorted_bonus
        self._source_sorted_penalty = source_sorted_penalty
        self._source_unlock_bonus = source_unlock_bonus
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._dest_headroom_weight = dest_headroom_weight
        self._c_top_weight = c_top_weight

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        selected = []
        valid = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            if not partial.stacks[so] or len(partial.stacks[sd]) >= partial.H:
                continue
            c = partial.stacks[so][-1]
            valid.append(action)
            source_sorted = partial.sorted_n[so] == len(partial.stacks[so])
            dest_sorted = partial.sorted_n[sd] == len(partial.stacks[sd])
            dest_accepts_sorted = c <= partial.g(sd)
            source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
            source_ub = partial.ub(so)
            if dest_sorted and dest_accepts_sorted:
                selected.append(action)
                continue
            if source_bad > 0 and (dest_accepts_sorted or not partial.stacks[sd]):
                selected.append(action)
                continue
            if source_ub > 0 and (dest_accepts_sorted or dest_sorted):
                selected.append(action)
                continue
            if source_sorted and (not dest_sorted) and (not dest_accepts_sorted):
                continue
        if selected:
            return selected
        return valid

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        c = partial.stacks[so][-1]
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        created_bad = max(0, resulting_bad - partial.bad())
        source_sorted = 1.0 if partial.sorted_n[so] == len(partial.stacks[so]) else 0.0
        source_bad = float(len(partial.stacks[so]) - partial.sorted_n[so])
        source_ub = float(partial.ub(so))
        dest_sorted_before = 1.0 if partial.sorted_n[sd] == len(partial.stacks[sd]) else 0.0
        dest_sorted_after = 1.0 if nxt.sorted_n[sd] == len(nxt.stacks[sd]) else 0.0
        dest_safe_before = 1.0 if dest_sorted_before and c <= partial.g(sd) else 0.0
        dest_safe_after = 1.0 if dest_sorted_after else 0.0
        dest_free = float(partial.e(sd))
        dest_top = float(partial.g(sd))
        headroom_after = float(nxt.e(sd))
        score = 0.0
        score += resulting_bad * self._source_bad_weight
        score += created_bad * self._created_bad_weight
        score -= dest_safe_before * self._dest_safe_bonus
        score -= dest_safe_after * self._dest_sorted_bonus
        score -= source_bad * self._auto_safe_unlock_to_sorted_stack_score_k1
        score -= source_ub * self._source_unlock_bonus
        score += source_sorted * self._source_sorted_penalty
        score += dest_free * self._dest_free_weight
        score += dest_top * self._dest_top_weight
        score += headroom_after * self._dest_headroom_weight
        score -= c * self._c_top_weight
        return float(score)

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeUnlockToSortedStackRefinedRuleV4(**params)])
_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 10.0, 'safe_unlock_to_sorted_stack_score_k2': 0.01}
_AUTO_OWNER = {'safe_unlock_to_sorted_stack_score_k1': 'SafeUnlockToSortedStackRefinedRuleV4', 'safe_unlock_to_sorted_stack_score_k2': 'SafeUnlockToSortedStackRefinedRuleV4'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeUnlockToSortedStackRefinedRuleV4': SafeUnlockToSortedStackRefinedRuleV4}
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
