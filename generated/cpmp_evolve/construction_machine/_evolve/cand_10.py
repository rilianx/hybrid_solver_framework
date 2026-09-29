COMPONENT = {'name': 'safe_unlock_to_sorted_stack_macro_refine', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 2000.0], 'default': 800.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 8.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'safe_unlock_to_sorted_stack_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStackRefinedMacro:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_score_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, source_bad_weight: float=800.0, dest_free_weight: float=8.0, dest_top_weight: float=1.0, safe_dest_bonus: float=18.0, source_sorted_bonus: float=10.0, created_bad_weight: float=120.0, ub_weight: float=30.0, exact_sort_bonus: float=25.0):
        self._source_bad_weight = source_bad_weight
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._safe_dest_bonus = safe_dest_bonus
        self._source_sorted_bonus = source_sorted_bonus
        self._created_bad_weight = created_bad_weight
        self._ub_weight = ub_weight
        self._exact_sort_bonus = exact_sort_bonus

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        candidates = getattr(partial, 'visited', None)
        return memory

    def done(self, partial, memory):
        return False

    def _is_safe_dest(self, partial, action):
        so, sd = (action.so, action.sd)
        if not partial.stacks[so]:
            return False
        if len(partial.stacks[sd]) >= partial.H:
            return False
        c = partial.stacks[so][-1]
        return partial.sorted_n[sd] == len(partial.stacks[sd]) and c <= partial.g(sd)

    def _is_source_sorted(self, partial, so):
        return partial.sorted_n[so] == len(partial.stacks[so])

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        safe_dest = [a for a in candidates if self._is_safe_dest(partial, a)]
        if safe_dest:
            return safe_dest
        improving = []
        for a in candidates:
            so, sd = (a.so, a.sd)
            if not partial.stacks[so] or len(partial.stacks[sd]) >= partial.H:
                continue
            c = partial.stacks[so][-1]
            nxt = partial.copy()
            nxt.move(so, sd)
            if nxt.bad() <= partial.bad():
                improving.append(a)
        if improving:
            return improving
        fallback = []
        for a in candidates:
            so, sd = (a.so, a.sd)
            if not partial.stacks[so] or len(partial.stacks[sd]) >= partial.H:
                continue
            c = partial.stacks[so][-1]
            if partial.sorted_n[sd] == len(partial.stacks[sd]) or c <= partial.g(sd):
                fallback.append(a)
        return fallback

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        if not partial.stacks[so] or len(partial.stacks[sd]) >= partial.H:
            return float('inf')
        c = partial.stacks[so][-1]
        nxt = partial.copy()
        nxt.move(so, sd)
        resulting_bad = nxt.bad()
        created_bad = max(0, resulting_bad - partial.bad())
        dest_is_safe = 1.0 if self._is_safe_dest(partial, action) else 0.0
        source_is_sorted = 1.0 if self._is_source_sorted(partial, so) else 0.0
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        ub_after = nxt.ub(sd)
        score = resulting_bad * self._source_bad_weight + created_bad * self._created_bad_weight + ub_after * self._ub_weight - dest_is_safe * self._safe_dest_bonus - source_is_sorted * self._source_sorted_bonus - (1.0 if nxt.is_sorted_stack(sd) else 0.0) * self._exact_sort_bonus + source_bad * self._auto_safe_unlock_to_sorted_stack_score_k1 + dest_free * self._dest_free_weight + dest_top * self._dest_top_weight - c * self._auto_safe_unlock_to_sorted_stack_score_k2
        return float(score)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeUnlockToSortedStackRefinedMacro(**params)])
_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 10.0, 'safe_unlock_to_sorted_stack_score_k2': 0.01}
_AUTO_OWNER = {'safe_unlock_to_sorted_stack_score_k1': 'SafeUnlockToSortedStackRefinedMacro', 'safe_unlock_to_sorted_stack_score_k2': 'SafeUnlockToSortedStackRefinedMacro'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeUnlockToSortedStackRefinedMacro': SafeUnlockToSortedStackRefinedMacro}
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
