COMPONENT = {'name': 'drain_bad_stack_macro_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStack:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_score_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, safe_dest_bonus: float=12.0, source_sorted_bonus: float=8.0, source_bad_weight: float=1000.0, dest_free_weight: float=10.0, dest_top_weight: float=1.0, created_bad_weight: float=200.0):
        self._safe_dest_bonus = safe_dest_bonus
        self._source_sorted_bonus = source_sorted_bonus
        self._source_bad_weight = source_bad_weight
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._created_bad_weight = created_bad_weight

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        allowed = []
        for action in candidates:
            so, sd = (action.so, action.sd)
            if not partial.stacks[so]:
                continue
            if len(partial.stacks[sd]) >= partial.H:
                continue
            c = partial.stacks[so][-1]
            if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd):
                allowed.append(action)
                continue
            if partial.sorted_n[so] == len(partial.stacks[so]):
                if c > partial.g(sd) or not partial.stacks[sd]:
                    allowed.append(action)
                continue
            if c >= partial.g(sd) or partial.sorted_n[sd] == len(partial.stacks[sd]):
                allowed.append(action)
        return allowed

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
        score = resulting_bad * self._source_bad_weight + created_bad * self._created_bad_weight - dest_is_safe * self._safe_dest_bonus - source_is_sorted * self._source_sorted_bonus + source_bad * self._auto_safe_unlock_to_sorted_stack_score_k1 + dest_free * self._dest_free_weight + dest_top * self._dest_top_weight - c * self._auto_safe_unlock_to_sorted_stack_score_k2
        return float(score)

class DrainBadStackMacro:
    name = 'drain_bad_stack_macro'
    priority = 120

    def __init__(self, source_ub_weight: float=50.0, source_bad_weight: float=1000.0, dest_free_weight: float=10.0, dest_top_weight: float=1.0, safe_dest_bonus: float=12.0, source_sorted_bonus: float=8.0, created_bad_weight: float=200.0):
        self._source_ub_weight = source_ub_weight
        self._source_bad_weight = source_bad_weight
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._safe_dest_bonus = safe_dest_bonus
        self._source_sorted_bonus = source_sorted_bonus
        self._created_bad_weight = created_bad_weight

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best = None
        best_key = None
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
            source_ub = partial.ub(so)
            if source_bad <= 0 and source_ub <= 0:
                continue
            top = partial.stacks[so][-1]
            for sd in range(partial.S):
                if so == sd or len(partial.stacks[sd]) >= partial.H:
                    continue
                safe = 1 if partial.sorted_n[sd] == len(partial.stacks[sd]) and top <= partial.g(sd) else 0
                free = partial.e(sd)
                key = (safe, source_ub, source_bad, free, -partial.g(sd), -sd, -so)
                if best_key is None or key > best_key:
                    best_key = key
                    best = (so, sd)
        return best if best is not None else ()

    def done(self, partial, memory):
        if not memory:
            return True
        so, sd = memory
        if so >= partial.S or sd >= partial.S:
            return True
        if not partial.stacks[so]:
            return True
        if len(partial.stacks[sd]) >= partial.H:
            return True
        if partial.is_sorted_stack(so):
            return True
        return False

    def allowed(self, partial, memory, candidates):
        if not memory or not candidates:
            return []
        so, sd = memory
        allowed = []
        for action in candidates:
            if action.so != so or action.sd != sd:
                continue
            if not partial.valid(action.so, action.sd):
                continue
            c = partial.stacks[action.so][-1]
            if partial.sorted_n[action.sd] == len(partial.stacks[action.sd]) and c <= partial.g(action.sd):
                allowed.append(action)
                continue
            if partial.sorted_n[action.so] != len(partial.stacks[action.so]):
                if c >= partial.g(action.sd) or partial.sorted_n[action.sd] == len(partial.stacks[action.sd]):
                    allowed.append(action)
        return allowed

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
        source_ub = partial.ub(so)
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        score = resulting_bad * self._source_bad_weight + created_bad * self._created_bad_weight - dest_is_safe * self._safe_dest_bonus - source_is_sorted * self._source_sorted_bonus + source_bad * self._source_bad_weight + source_ub * self._source_ub_weight + dest_free * self._dest_free_weight + dest_top * self._dest_top_weight - c
        return float(score)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    macro = DrainBadStackMacro(source_ub_weight=params.get('source_ub_weight', 50.0), source_bad_weight=params.get('source_bad_weight', 1000.0), dest_free_weight=params.get('dest_free_weight', 10.0), dest_top_weight=params.get('dest_top_weight', 1.0), safe_dest_bonus=params.get('safe_dest_bonus', 12.0), source_sorted_bonus=params.get('source_sorted_bonus', 8.0), created_bad_weight=params.get('created_bad_weight', 200.0))
    simple = SafeUnlockToSortedStack(safe_dest_bonus=params.get('safe_dest_bonus', 12.0), source_sorted_bonus=params.get('source_sorted_bonus', 8.0), source_bad_weight=params.get('source_bad_weight', 1000.0), dest_free_weight=params.get('dest_free_weight', 10.0), dest_top_weight=params.get('dest_top_weight', 1.0), created_bad_weight=params.get('created_bad_weight', 200.0))
    return RuleMachine(problem, [macro, simple])
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
