COMPONENT = {'name': 'safe_unlock_to_sorted_stack_targeted_macro', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 2000.0], 'default': 1000.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 10.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'unsafe_dest_penalty': {'type': 'float', 'range': [0.0, 500.0], 'default': 250.0}}}
from core.rules import RuleMachine

class SafeUnlockToSortedStack:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10.0
    _auto_safe_unlock_to_sorted_stack_score_k2 = 0.01
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def __init__(self, safe_dest_bonus: float=12.0, source_sorted_bonus: float=8.0, source_bad_weight: float=1000.0, dest_free_weight: float=10.0, dest_top_weight: float=1.0, created_bad_weight: float=200.0, unlock_gain_weight: float=40.0, unsafe_dest_penalty: float=250.0, source_focus_bonus: float=15.0):
        self._safe_dest_bonus = safe_dest_bonus
        self._source_sorted_bonus = source_sorted_bonus
        self._source_bad_weight = source_bad_weight
        self._dest_free_weight = dest_free_weight
        self._dest_top_weight = dest_top_weight
        self._created_bad_weight = created_bad_weight
        self._unlock_gain_weight = unlock_gain_weight
        self._unsafe_dest_penalty = unsafe_dest_penalty
        self._source_focus_bonus = source_focus_bonus

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best_so = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            bad_i = len(s) - partial.sorted_n[i]
            if bad_i <= 0:
                continue
            key = (-bad_i, -partial.ub(i), -len(s), i)
            if best_key is None or key < best_key:
                best_key = key
                best_so = i
        if best_so is None:
            return (-1,)
        return (best_so,)

    def done(self, partial, memory):
        if not memory or memory[0] < 0:
            return True
        so = memory[0]
        if so >= len(partial.stacks):
            return True
        return len(partial.stacks[so]) == partial.sorted_n[so]

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        so_focus = memory[0] if memory else -1
        allowed = []
        if so_focus is not None and 0 <= so_focus < len(partial.stacks):
            for action in candidates:
                if action.so != so_focus:
                    continue
                if not partial.stacks[action.so]:
                    continue
                if len(partial.stacks[action.sd]) >= partial.H:
                    continue
                allowed.append(action)
            if allowed:
                return allowed
        best_so = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            bad_i = len(s) - partial.sorted_n[i]
            if bad_i <= 0:
                continue
            key = (-bad_i, -partial.ub(i), -len(s), i)
            if best_key is None or key < best_key:
                best_key = key
                best_so = i
        if best_so is None:
            return []
        for action in candidates:
            if action.so != best_so:
                continue
            if not partial.stacks[action.so]:
                continue
            if len(partial.stacks[action.sd]) >= partial.H:
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
        source_is_sorted = 1.0 if partial.sorted_n[so] == len(partial.stacks[so]) else 0.0
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        unlock_gain = max(0, partial.ub(so) - max(0, len(nxt.stacks[so]) - nxt.sorted_n[so]))
        dest_free = partial.e(sd)
        dest_top = partial.g(sd)
        unsafe_dest = 1.0 if c > partial.g(sd) and partial.stacks[sd] else 0.0
        focus_bonus = 1.0 if memory and memory[0] == so else 0.0
        score = resulting_bad * self._source_bad_weight + created_bad * self._created_bad_weight - dest_is_safe * self._safe_dest_bonus - source_is_sorted * self._source_sorted_bonus - unlock_gain * self._unlock_gain_weight + source_bad * self._auto_safe_unlock_to_sorted_stack_score_k1 + dest_free * self._dest_free_weight + dest_top * self._dest_top_weight - c * self._auto_safe_unlock_to_sorted_stack_score_k2 + unsafe_dest * self._unsafe_dest_penalty - focus_bonus * self._source_focus_bonus
        return float(score)

    def update(self, partial, memory, action):
        if not memory:
            return self.start(partial, memory)
        so_focus = memory[0]
        if so_focus < 0:
            return memory
        if action.so != so_focus:
            return memory
        if action.so >= len(partial.stacks):
            return memory
        if len(partial.stacks[action.so]) == partial.sorted_n[action.so]:
            return (action.so,)
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
