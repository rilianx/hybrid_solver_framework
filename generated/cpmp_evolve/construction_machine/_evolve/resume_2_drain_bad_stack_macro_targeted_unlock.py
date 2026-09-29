COMPONENT = {'name': 'drain_bad_stack_macro_targeted_unlock', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'result_bad_weight': {'type': 'float', 'range': [0.0, 10000.0], 'default': 1000.0}, 'unsorted_dest_penalty': {'type': 'float', 'range': [0.0, 1000.0], 'default': 25.0}, 'targeted_unlock_source_bad_weight': {'type': 'float', 'range': [0.0, 50.0], 'default': 8.0}, 'safe_unlock_to_sorted_stack_score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}, 'safe_unlock_to_sorted_stack_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}, 'drain_bad_stack_macro_score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}, 'drain_bad_stack_macro_score_k2': {'type': 'float', 'range': [0.0, 16.0], 'default': 8.0}, 'targeted_unlock_macro_score_k1': {'type': 'float', 'range': [0.0, 10.0], 'default': 5.0}, 'targeted_unlock_macro_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}, 'created_bad_weight': {'type': 'float', 'range': [0.0, 400.0], 'default': 200.0}, 'safe_dest_bonus': {'type': 'float', 'range': [0.0, 24.0], 'default': 12.0}, 'empty_dest_bonus': {'type': 'float', 'range': [0.0, 12.0], 'default': 6.0}, 'source_top_weight': {'type': 'float', 'range': [0.0, 4.0], 'default': 2.0}, 'source_ub_weight': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}, 'targeted_unlock_dest_bonus': {'type': 'float', 'range': [0.0, 30.0], 'default': 15.0}, 'targeted_unlock_source_ub_weight': {'type': 'float', 'range': [0.0, 12.0], 'default': 6.0}, 'safe_unlock_to_sorted_stack_source_sorted_bonus': {'type': 'float', 'range': [0.0, 16.0], 'default': 8.0}, 'safe_unlock_to_sorted_stack_dest_free_weight': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}}}
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
    _auto_drain_bad_stack_macro_score_k1 = 10.0
    _auto_drain_bad_stack_macro_score_k2 = 8.0
    name = 'drain_bad_stack_macro'
    priority = 120

    def __init__(self, result_bad_weight: float=1000.0, created_bad_weight: float=200.0, safe_dest_bonus: float=12.0, empty_dest_bonus: float=6.0, unsorted_dest_penalty: float=25.0, source_top_weight: float=2.0, source_ub_weight: float=10.0, safe_source_guard: bool=True):
        self._result_bad_weight = result_bad_weight
        self._created_bad_weight = created_bad_weight
        self._safe_dest_bonus = safe_dest_bonus
        self._empty_dest_bonus = empty_dest_bonus
        self._unsorted_dest_penalty = unsorted_dest_penalty
        self._source_top_weight = source_top_weight
        self._source_ub_weight = source_ub_weight
        self._safe_source_guard = safe_source_guard

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
            key = (source_ub, source_bad, top, -len(partial.stacks[so]), -so)
            if best_key is None or key > best_key:
                best_key = key
                best = so
        return best if best is not None else ()

    def done(self, partial, memory):
        if not memory:
            return True
        so = memory
        if so >= partial.S:
            return True
        if not partial.stacks[so]:
            return True
        if partial.is_sorted_stack(so):
            return True
        if self._safe_source_guard and partial.ub(so) <= 0 and (len(partial.stacks[so]) - partial.sorted_n[so] <= 0):
            return True
        return False

    def allowed(self, partial, memory, candidates):
        if not memory or not candidates:
            return []
        so = memory
        if so >= partial.S or not partial.stacks[so]:
            return []
        allowed = []
        for action in candidates:
            if action.so != so:
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
        dest_sorted = partial.sorted_n[sd] == len(partial.stacks[sd])
        source_sorted = partial.sorted_n[so] == len(partial.stacks[so])
        safe_dest = 1.0 if dest_sorted and c <= partial.g(sd) else 0.0
        empty_dest = 1.0 if not partial.stacks[sd] else 0.0
        unsorted_dest = 1.0 if partial.stacks[sd] and (not dest_sorted) else 0.0
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        source_ub = partial.ub(so)
        source_top = c
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        score = resulting_bad * self._result_bad_weight + created_bad * self._created_bad_weight - safe_dest * self._safe_dest_bonus - empty_dest * self._empty_dest_bonus + unsorted_dest * self._unsorted_dest_penalty + source_bad * self._source_ub_weight + source_ub * self._source_ub_weight - source_top * self._source_top_weight + dest_free * self._auto_drain_bad_stack_macro_score_k1 + dest_top * 1.0 - source_sorted * self._auto_drain_bad_stack_macro_score_k2
        return float(score)

    def update(self, partial, memory, action):
        return memory

class TargetedUnlockMacro:
    _auto_targeted_unlock_macro_score_k1 = 5.0
    _auto_targeted_unlock_macro_score_k2 = 0.01
    name = 'targeted_unlock_macro'
    priority = 110

    def __init__(self, dest_bonus: float=15.0, source_bad_weight: float=8.0, source_ub_weight: float=6.0, created_bad_weight: float=200.0):
        self._dest_bonus = dest_bonus
        self._source_bad_weight = source_bad_weight
        self._source_ub_weight = source_ub_weight
        self._created_bad_weight = created_bad_weight

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best = None
        best_key = None
        for sd in range(partial.S):
            if len(partial.stacks[sd]) >= partial.H:
                continue
            if not partial.stacks[sd]:
                continue
            if partial.sorted_n[sd] != len(partial.stacks[sd]):
                continue
            key = (partial.e(sd), partial.g(sd), -sd)
            if best_key is None or key > best_key:
                best_key = key
                best = sd
        return best if best is not None else ()

    def done(self, partial, memory):
        if not memory:
            return True
        sd = memory
        if sd >= partial.S:
            return True
        if len(partial.stacks[sd]) >= partial.H:
            return True
        if not partial.stacks[sd]:
            return True
        if partial.sorted_n[sd] != len(partial.stacks[sd]):
            return True
        return False

    def allowed(self, partial, memory, candidates):
        if not memory or not candidates:
            return []
        sd = memory
        if sd >= partial.S or len(partial.stacks[sd]) >= partial.H:
            return []
        allowed = []
        for action in candidates:
            if action.sd != sd:
                continue
            if not partial.valid(action.so, action.sd):
                continue
            c = partial.stacks[action.so][-1]
            if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd):
                allowed.append(action)
            elif partial.sorted_n[action.so] == len(partial.stacks[action.so]) and (c > partial.g(sd) or not partial.stacks[sd]):
                allowed.append(action)
            elif c >= partial.g(sd) or partial.sorted_n[sd] == len(partial.stacks[sd]):
                allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        c = partial.stacks[so][-1]
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        created_bad = max(0, resulting_bad - partial.bad())
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        source_ub = partial.ub(so)
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        dest_sorted = 1.0 if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd) else 0.0
        score = resulting_bad * 1000.0 + created_bad * self._created_bad_weight - dest_sorted * self._dest_bonus + source_bad * self._source_bad_weight + source_ub * self._source_ub_weight + dest_free * self._auto_targeted_unlock_macro_score_k1 + dest_top * 1.0 - c * self._auto_targeted_unlock_macro_score_k2
        return float(score)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    macro = DrainBadStackMacro(result_bad_weight=params.get('result_bad_weight', 1000.0), created_bad_weight=params.get('created_bad_weight', 200.0), safe_dest_bonus=params.get('safe_dest_bonus', 12.0), empty_dest_bonus=params.get('empty_dest_bonus', 6.0), unsorted_dest_penalty=params.get('unsorted_dest_penalty', 25.0), source_top_weight=params.get('source_top_weight', 2.0), source_ub_weight=params.get('source_ub_weight', 10.0), safe_source_guard=True)
    targeted = TargetedUnlockMacro(dest_bonus=params.get('targeted_unlock_dest_bonus', 15.0), source_bad_weight=params.get('targeted_unlock_source_bad_weight', 8.0), source_ub_weight=params.get('targeted_unlock_source_ub_weight', 6.0), created_bad_weight=params.get('created_bad_weight', 200.0))
    simple = SafeUnlockToSortedStack(safe_dest_bonus=params.get('safe_dest_bonus', 12.0), source_sorted_bonus=params.get('safe_unlock_to_sorted_stack_source_sorted_bonus', 8.0), source_bad_weight=1000.0, dest_free_weight=params.get('safe_unlock_to_sorted_stack_dest_free_weight', 10.0), dest_top_weight=1.0, created_bad_weight=params.get('created_bad_weight', 200.0))
    return RuleMachine(problem, [macro, targeted, simple])

_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 10.0, 'safe_unlock_to_sorted_stack_score_k2': 0.01, 'drain_bad_stack_macro_score_k1': 10.0, 'drain_bad_stack_macro_score_k2': 8.0, 'targeted_unlock_macro_score_k1': 5.0, 'targeted_unlock_macro_score_k2': 0.01}
_AUTO_OWNER = {'safe_unlock_to_sorted_stack_score_k1': 'SafeUnlockToSortedStack', 'safe_unlock_to_sorted_stack_score_k2': 'SafeUnlockToSortedStack', 'drain_bad_stack_macro_score_k1': 'DrainBadStackMacro', 'drain_bad_stack_macro_score_k2': 'DrainBadStackMacro', 'targeted_unlock_macro_score_k1': 'TargetedUnlockMacro', 'targeted_unlock_macro_score_k2': 'TargetedUnlockMacro'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'DrainBadStackMacro': DrainBadStackMacro, 'SafeUnlockToSortedStack': SafeUnlockToSortedStack, 'TargetedUnlockMacro': TargetedUnlockMacro}
_AUTO_FACTORY = '_build_component_llm'

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT; `_AUTO_OWNER`: la clase de cada uno). Se fijan en las clases
    mientras se construye (por si un `__init__` los usa) y en cada instancia: la máquina, sus
    reglas y sus transiciones."""
    attrs = globals().get("_AUTO_ATTR", {})  # parámetro -> atributo de la instancia (los defaults de un __init__)
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    lifted = [k for k in auto if k not in attrs]
    saved = {k: getattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k) for k in lifted}
    for k in lifted:
        setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k, auto[k])
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k, v)
    parts = [obj, getattr(obj, "transitions", None), *list(getattr(obj, "rules", None) or [])]
    for part in parts:
        for k, v in auto.items():
            if part is not None and isinstance(part, _AUTO_CLASSES[_AUTO_OWNER[k]]):
                setattr(part, attrs.get(k, "_auto_" + k), v)
    return obj
