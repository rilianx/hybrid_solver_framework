COMPONENT = {'name': 'safe_unlock_to_sorted_stack_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class SafeUnlockToSortedStack:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 10
    _auto_safe_unlock_to_sorted_stack_score_k2 = 10
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def init(self, partial):
        return self.start(partial, ())

    def start(self, partial, memory):
        source = self._pick_source(partial)
        return (source,)

    def done(self, partial, memory):
        if not memory:
            return True
        source = memory[0]
        if source < 0 or source >= partial.S:
            return True
        if partial.sorted_n[source] == len(partial.stacks[source]):
            return True
        return False

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        source = memory[0] if memory else self._pick_source(partial)
        if source is None:
            return []
        from_source = [a for a in candidates if a.so == source]
        if not from_source:
            return []
        safe = [a for a in from_source if partial.sorted_n[a.sd] == len(partial.stacks[a.sd]) and partial.g(a.sd) >= partial.stacks[a.so][-1]]
        return safe if safe else from_source

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        c = partial.stacks[so][-1]
        source_bad = len(partial.stacks[so]) - partial.sorted_n[so]
        source_ub = partial.ub(so)
        dest_sorted = partial.sorted_n[sd] == len(partial.stacks[sd])
        dest_top = partial.g(sd)
        dest_free = partial.e(sd)
        dest_height = partial.h(sd)
        if dest_sorted and c <= dest_top:
            return float(source_bad * 100000 + source_ub * 10000 - dest_top * 100 - dest_free * self._auto_safe_unlock_to_sorted_stack_score_k1 - dest_height + c)
        return float(source_bad * 100000 + source_ub * 10000 + dest_top * 100 + dest_height * self._auto_safe_unlock_to_sorted_stack_score_k2 - dest_free - c)

    def update(self, partial, memory, action):
        source = memory[0] if memory else self._pick_source(partial)
        if source is None:
            return ()
        if partial.sorted_n[source] == len(partial.stacks[source]):
            return ()
        return (source,)

    def _pick_source(self, partial):
        best = None
        best_key = None
        for i in range(partial.S):
            if not partial.stacks[i]:
                continue
            bad = len(partial.stacks[i]) - partial.sorted_n[i]
            ub = partial.ub(i)
            if bad <= 0 and ub <= 0:
                continue
            key = (bad, ub, len(partial.stacks[i]), -i)
            if best_key is None or key > best_key:
                best_key = key
                best = i
        return best

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeUnlockToSortedStack()])
_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 10, 'safe_unlock_to_sorted_stack_score_k2': 10}
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
