COMPONENT = {'name': 'targeted_unlock_macro_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'targeted_unlock_dest_free_weight': {'type': 'float', 'range': [0.0, 20.0], 'default': 5.0}}}
from core.rules import RuleMachine

class TargetedUnlockMacro:
    _auto_targeted_unlock_macro_score_k1 = 0.01
    name = 'targeted_unlock_macro'
    priority = 1000

    def __init__(self, source_bad_weight: float=8.0, dest_bonus: float=15.0, created_bad_weight: float=200.0, dest_free_weight: float=5.0):
        self._source_bad_weight = source_bad_weight
        self._dest_bonus = dest_bonus
        self._created_bad_weight = created_bad_weight
        self._dest_free_weight = dest_free_weight

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
            key = (source_ub, source_bad, len(partial.stacks[so]), top, -so)
            if best_key is None or key > best_key:
                best_key = key
                best = so
        return best if best is not None else ()

    def done(self, partial, memory):
        if not memory:
            return True
        so = memory
        if so >= partial.S or not partial.stacks[so]:
            return True
        if partial.is_sorted_stack(so):
            return True
        if partial.ub(so) <= 0 and len(partial.stacks[so]) - partial.sorted_n[so] <= 0:
            return True
        return False

    def allowed(self, partial, memory, candidates):
        if not memory or not candidates:
            return []
        so = memory
        if so >= partial.S or not partial.stacks[so]:
            return []
        c = partial.stacks[so][-1]
        allowed = []
        for action in candidates:
            if action.so != so:
                continue
            if not partial.valid(action.so, action.sd):
                continue
            sd = action.sd
            if partial.stacks[sd]:
                if c == partial.stacks[sd][-1]:
                    allowed.append(action)
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
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        source_ub = partial.ub(so)
        dest_free = partial.e(sd)
        dest_sorted = 1.0 if partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd) else 0.0
        score = resulting_bad * 1000.0 + created_bad * self._created_bad_weight - dest_sorted * self._dest_bonus + source_bad * self._source_bad_weight + source_ub * self._source_bad_weight + dest_free * self._dest_free_weight - c * self._auto_targeted_unlock_macro_score_k1
        return float(score)

    def update(self, partial, memory, action):
        return memory

class FallbackDrainBadStackMacro:
    name = 'fallback_drain_bad_stack_macro'
    priority = 100

    def __init__(self, result_bad_weight: float=1000.0, unsorted_dest_penalty: float=25.0):
        self._result_bad_weight = result_bad_weight
        self._unsorted_dest_penalty = unsorted_dest_penalty

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
        if so >= partial.S or not partial.stacks[so]:
            return True
        if partial.is_sorted_stack(so):
            return True
        if partial.ub(so) <= 0 and len(partial.stacks[so]) - partial.sorted_n[so] <= 0:
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
            if partial.valid(action.so, action.sd):
                allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        dest_unsorted = 1.0 if partial.stacks[sd] and partial.sorted_n[sd] != len(partial.stacks[sd]) else 0.0
        return float(resulting_bad * self._result_bad_weight + dest_unsorted * self._unsorted_dest_penalty)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    targeted = TargetedUnlockMacro(source_bad_weight=params.get('targeted_unlock_source_bad_weight', 8.0), dest_bonus=params.get('targeted_unlock_dest_bonus', 15.0), created_bad_weight=params.get('targeted_unlock_created_bad_weight', 200.0), dest_free_weight=params.get('targeted_unlock_dest_free_weight', 5.0))
    fallback = FallbackDrainBadStackMacro(result_bad_weight=params.get('fallback_result_bad_weight', 1000.0), unsorted_dest_penalty=params.get('fallback_unsorted_dest_penalty', 25.0))
    return RuleMachine(problem, [targeted, fallback])
_AUTO = {'targeted_unlock_macro_score_k1': 0.01}
_AUTO_OWNER = {'targeted_unlock_macro_score_k1': 'TargetedUnlockMacro'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'TargetedUnlockMacro': TargetedUnlockMacro}
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
