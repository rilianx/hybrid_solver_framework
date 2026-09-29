COMPONENT = {'name': 'safe_unlock_to_sorted_stack_refined_rule_v3', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 1000.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 10.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'safe_unlock_to_sorted_stack_init_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}, 'safe_unlock_to_sorted_stack_init_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStackRule:
    _auto_safe_unlock_to_sorted_stack_init_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_init_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, safe_dest_bonus: float=12.0, source_sorted_bonus: float=8.0, source_bad_weight: float=1000.0, dest_free_weight: float=10.0, dest_top_weight: float=1.0, created_bad_weight: float=200.0, nonempty_dest_penalty: float=6.0, unsafe_dest_penalty: float=25.0, buffer_bonus: float=5.0):
        self._safe_dest_bonus = safe_dest_bonus
        self._source_sorted_bonus = source_sorted_bonus
        self._source_bad_weight = source_bad_weight
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._created_bad_weight = created_bad_weight
        self._nonempty_dest_penalty = nonempty_dest_penalty
        self._unsafe_dest_penalty = unsafe_dest_penalty
        self._buffer_bonus = buffer_bonus
        self._k1 = self._auto_safe_unlock_to_sorted_stack_init_k1
        self._k2 = self._auto_safe_unlock_to_sorted_stack_init_k2

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        safe = []
        productive = []
        fallback = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            if not partial.stacks[so]:
                continue
            if len(partial.stacks[sd]) >= partial.H:
                continue
            c = partial.stacks[so][-1]
            src_sorted = partial.sorted_n[so] == len(partial.stacks[so])
            dst_sorted = partial.sorted_n[sd] == len(partial.stacks[sd])
            safe_dest = dst_sorted and c <= partial.g(sd)
            can_keep_destination_safe = c <= partial.g(sd)
            if safe_dest:
                safe.append(action)
                continue
            creates_bad = not can_keep_destination_safe
            if src_sorted and (not creates_bad) or (not src_sorted and can_keep_destination_safe):
                productive.append(action)
                continue
            if can_keep_destination_safe or partial.e(sd) > 0:
                fallback.append(action)
        if safe:
            return safe
        if productive:
            return productive
        return fallback

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        c = partial.stacks[so][-1]
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        created_bad = max(0, resulting_bad - partial.bad())
        dest_sorted = 1.0 if partial.sorted_n[sd] == len(partial.stacks[sd]) else 0.0
        src_sorted = 1.0 if partial.sorted_n[so] == len(partial.stacks[so]) else 0.0
        safe_dest = 1.0 if dest_sorted and c <= partial.g(sd) else 0.0
        can_keep_destination_safe = 1.0 if c <= partial.g(sd) else 0.0
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        score = 0.0
        score += resulting_bad * self._source_bad_weight
        score += created_bad * self._created_bad_weight
        score += source_bad * self._k1
        score += dest_free * self._dest_free_weight
        score += dest_top * self._dest_top_weight
        score -= safe_dest * self._safe_dest_bonus
        score -= src_sorted * self._source_sorted_bonus
        score -= can_keep_destination_safe * self._buffer_bonus
        score -= (1.0 - safe_dest) * self._unsafe_dest_penalty
        score -= (1.0 - dest_sorted) * self._nonempty_dest_penalty
        score -= c * self._k2
        return float(score)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    rule = SafeUnlockToSortedStackRule(safe_dest_bonus=params.get('safe_unlock_to_sorted_stack_safe_dest_bonus', 12.0), source_sorted_bonus=params.get('safe_unlock_to_sorted_stack_source_sorted_bonus', 8.0), source_bad_weight=params.get('source_bad_weight', 1000.0), dest_free_weight=params.get('dest_free_weight', 10.0), dest_top_weight=params.get('dest_top_weight', 1.0), created_bad_weight=params.get('safe_unlock_to_sorted_stack_created_bad_weight', 200.0), nonempty_dest_penalty=params.get('safe_unlock_to_sorted_stack_nonempty_dest_penalty', 6.0), unsafe_dest_penalty=params.get('safe_unlock_to_sorted_stack_unsafe_dest_penalty', 25.0), buffer_bonus=params.get('safe_unlock_to_sorted_stack_buffer_bonus', 5.0))
    return RuleMachine(problem, [rule])
_AUTO = {'safe_unlock_to_sorted_stack_init_k1': 10.0, 'safe_unlock_to_sorted_stack_init_k2': 0.01}
_AUTO_OWNER = {'safe_unlock_to_sorted_stack_init_k1': 'SafeUnlockToSortedStackRule', 'safe_unlock_to_sorted_stack_init_k2': 'SafeUnlockToSortedStackRule'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeUnlockToSortedStackRule': SafeUnlockToSortedStackRule}
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
