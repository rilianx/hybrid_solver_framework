COMPONENT = {'name': 'reduce_bad_stack_then_unlock', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'macro_sorted_dest_bonus': {'type': 'float', 'range': [0.0, 50.0], 'default': 10.0}, 'macro_resulting_bad_weight': {'type': 'float', 'range': [0.0, 2000.0], 'default': 1000.0}, 'macro_dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 8.0}, 'macro_dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}}}
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

class ReduceBadStackMacro:
    _auto_reduce_bad_stack_macro_score_k1 = 0.01
    name = 'reduce_bad_stack_macro'
    priority = 120

    def __init__(self, macro_safe_dest_bonus: float=14.0, macro_sorted_dest_bonus: float=10.0, macro_created_bad_weight: float=120.0, macro_resulting_bad_weight: float=1000.0, macro_dest_free_weight: float=8.0, macro_dest_top_weight: float=1.0, macro_source_penalty: float=0.5):
        self._macro_safe_dest_bonus = macro_safe_dest_bonus
        self._macro_sorted_dest_bonus = macro_sorted_dest_bonus
        self._macro_created_bad_weight = macro_created_bad_weight
        self._macro_resulting_bad_weight = macro_resulting_bad_weight
        self._macro_dest_free_weight = macro_dest_free_weight
        self._macro_dest_top_weight = macro_dest_top_weight
        self._macro_source_penalty = macro_source_penalty

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            if not s:
                continue
            if partial.sorted_n[i] == len(s):
                continue
            bad_i = len(s) - partial.sorted_n[i]
            ub_i = partial.ub(i)
            key = (ub_i, bad_i, len(s), -i)
            if best_key is None or key > best_key:
                best_key = key
                best = i
        return () if best is None else (best,)

    def done(self, partial, memory):
        if not memory:
            return True
        source = memory[0]
        return source >= partial.S or partial.is_sorted_stack(source) or (not partial.stacks[source])

    def allowed(self, partial, memory, candidates):
        if not memory:
            return []
        source = memory[0]
        allowed = []
        for action in candidates:
            if action.so != source:
                continue
            if not partial.valid(action.so, action.sd):
                continue
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
        dest_is_sorted = 1.0 if partial.sorted_n[sd] == len(partial.stacks[sd]) else 0.0
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        score = resulting_bad * self._macro_resulting_bad_weight + created_bad * self._macro_created_bad_weight - dest_is_safe * self._macro_safe_dest_bonus - dest_is_sorted * self._macro_sorted_dest_bonus + dest_free * self._macro_dest_free_weight + dest_top * self._macro_dest_top_weight + source_bad * self._macro_source_penalty - c * self._auto_reduce_bad_stack_macro_score_k1
        return float(score)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    macro = ReduceBadStackMacro(macro_safe_dest_bonus=params.get('macro_safe_dest_bonus', 14.0), macro_sorted_dest_bonus=params.get('macro_sorted_dest_bonus', 10.0), macro_created_bad_weight=params.get('macro_created_bad_weight', 120.0), macro_resulting_bad_weight=params.get('macro_resulting_bad_weight', 1000.0), macro_dest_free_weight=params.get('macro_dest_free_weight', 8.0), macro_dest_top_weight=params.get('macro_dest_top_weight', 1.0), macro_source_penalty=params.get('macro_source_penalty', 0.5))
    simple = SafeUnlockToSortedStack(source_bad_weight=params.get('source_bad_weight', 1000.0), dest_free_weight=params.get('dest_free_weight', 10.0), dest_top_weight=params.get('dest_top_weight', 1.0), created_bad_weight=params.get('created_bad_weight', 200.0))
    return RuleMachine(problem, [macro, simple])
_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 10.0, 'safe_unlock_to_sorted_stack_score_k2': 0.01, 'reduce_bad_stack_macro_score_k1': 0.01}
_AUTO_OWNER = {'safe_unlock_to_sorted_stack_score_k1': 'SafeUnlockToSortedStack', 'safe_unlock_to_sorted_stack_score_k2': 'SafeUnlockToSortedStack', 'reduce_bad_stack_macro_score_k1': 'ReduceBadStackMacro'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'ReduceBadStackMacro': ReduceBadStackMacro, 'SafeUnlockToSortedStack': SafeUnlockToSortedStack}
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
