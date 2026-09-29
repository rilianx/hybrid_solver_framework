COMPONENT = {'name': 'targeted_unlock_macro_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 1000.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 10.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'macro_source_bad_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 1000.0}, 'macro_dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 10.0}, 'macro_dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'macro_safe_bonus': {'type': 'float', 'range': [0.0, 100.0], 'default': 12.0}, 'safe_unlock_to_sorted_stack_score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}, 'safe_unlock_to_sorted_stack_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}, 'macro_sorted_source_bonus': {'type': 'float', 'range': [0.0, 16.0], 'default': 8.0}}}
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

class TargetedUnlockMacro:
    name = 'targeted_unlock_macro'
    priority = 150

    def __init__(self, macro_source_bad_weight: float=1000.0, macro_dest_free_weight: float=10.0, macro_dest_top_weight: float=1.0, macro_safe_bonus: float=12.0, macro_sorted_source_bonus: float=8.0):
        self._macro_source_bad_weight = macro_source_bad_weight
        self._macro_dest_free_weight = macro_dest_free_weight
        self._macro_dest_top_weight = macro_dest_top_weight
        self._macro_safe_bonus = macro_safe_bonus
        self._macro_sorted_source_bonus = macro_sorted_source_bonus

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best = None
        best_key = None
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
            if source_bad <= 0:
                continue
            c = partial.stacks[so][-1]
            for sd in range(partial.S):
                if so == sd or len(partial.stacks[sd]) >= partial.H:
                    continue
                if c > partial.g(sd) and partial.sorted_n[sd] != len(partial.stacks[sd]):
                    continue
                dest_free = partial.e(sd)
                dest_top = partial.g(sd)
                safe_dest = 1 if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd) else 0
                source_sorted = 1 if partial.sorted_n[so] == len(partial.stacks[so]) else 0
                key = -safe_dest * self._macro_safe_bonus - source_sorted * self._macro_sorted_source_bonus + source_bad * self._macro_source_bad_weight + dest_free * self._macro_dest_free_weight + dest_top * self._macro_dest_top_weight
                if best_key is None or key < best_key:
                    best_key = key
                    best = (so, sd)
        return best if best is not None else ()

    def allowed(self, partial, memory, candidates):
        if not memory or len(memory) != 2:
            return []
        so, sd = memory
        if not partial.stacks[so] or len(partial.stacks[sd]) >= partial.H:
            return []
        allowed = []
        for action in candidates:
            if action.so == so and action.sd == sd:
                allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        nxt = partial.copy()
        nxt.move(action.so, action.sd)
        return float(nxt.bad())

    def done(self, partial, memory):
        if not memory or len(memory) != 2:
            return True
        so, sd = memory
        if not partial.stacks[so]:
            return True
        return partial.sorted_n[so] == len(partial.stacks[so]) or len(partial.stacks[sd]) >= partial.H

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    rule = SafeUnlockToSortedStack(safe_dest_bonus=params.get('macro_safe_bonus', 12.0), source_sorted_bonus=params.get('macro_sorted_source_bonus', 8.0), source_bad_weight=params.get('source_bad_weight', 1000.0), dest_free_weight=params.get('dest_free_weight', 10.0), dest_top_weight=params.get('dest_top_weight', 1.0), created_bad_weight=params.get('safe_unlock_to_sorted_stack_created_bad_weight', 200.0))
    macro = TargetedUnlockMacro(macro_source_bad_weight=params.get('macro_source_bad_weight', 1000.0), macro_dest_free_weight=params.get('macro_dest_free_weight', 10.0), macro_dest_top_weight=params.get('macro_dest_top_weight', 1.0), macro_safe_bonus=params.get('macro_safe_bonus', 12.0), macro_sorted_source_bonus=params.get('macro_sorted_source_bonus', 8.0))
    return RuleMachine(problem, [macro, rule])
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
