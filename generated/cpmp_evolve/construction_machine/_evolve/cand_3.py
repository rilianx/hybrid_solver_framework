COMPONENT = {'name': 'safe_unlock_to_sorted_stack_refined_macro', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class SafeUnlockToSortedStack:
    _auto_safe_unlock_to_sorted_stack_score_k1 = 50000
    _auto_safe_unlock_to_sorted_stack_score_k2 = 10
    name = 'safe_unlock_to_sorted_stack'
    priority = 100

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best = None
        best_key = None
        for i in range(partial.S):
            if not partial.stacks[i]:
                continue
            if partial.sorted_n[i] == len(partial.stacks[i]):
                continue
            key = (partial.ub(i), len(partial.stacks[i]) - partial.sorted_n[i], partial.h(i), partial.g(i), -i)
            if best is None or key > best_key:
                best = i
                best_key = key
        return (best,)

    def done(self, partial, memory):
        if not memory or memory[0] is None:
            return True
        so = memory[0]
        return so < 0 or so >= partial.S or partial.sorted_n[so] == len(partial.stacks[so])

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        source = memory[0] if memory else None
        if source is not None and (source < 0 or source >= partial.S):
            return []
        if source is not None:
            chosen = [a for a in candidates if a.so == source]
            if chosen:
                return chosen
        allowed = []
        for action in candidates:
            so = action.so
            if partial.sorted_n[so] < len(partial.stacks[so]):
                allowed.append(action)
        return allowed

    @staticmethod
    def _count_sorted(stack):
        n = 1 if stack else 0
        while n < len(stack) and stack[n] <= stack[n - 1]:
            n += 1
        return n

    def _simulate(self, partial, action):
        stacks = [list(s) for s in partial.stacks]
        c = stacks[action.so].pop()
        stacks[action.sd].append(c)
        bad = 0
        ub = 0
        for s in stacks:
            n = self._count_sorted(s)
            bad += len(s) - n
            if n < len(s):
                j = len(s) - 1
                count = 1
                while j - 1 >= n and s[j - 1] >= s[j]:
                    j -= 1
                    count += 1
                ub += count
        return (bad, ub, len(stacks[action.sd]))

    def score(self, partial, memory, action):
        result_bad, result_ub, dest_h = self._simulate(partial, action)
        dest = action.sd
        dest_top = partial.g(dest)
        source = action.so
        source_bad = len(partial.stacks[source]) - partial.sorted_n[source]
        source_bias = 0 if not memory or memory[0] is None or memory[0] == source else 1000000
        safe_dest = 1 if partial.sorted_n[dest] == len(partial.stacks[dest]) and partial.stacks[source][-1] <= dest_top else 0
        return float(source_bias + result_bad * 100000 + result_ub * 1000 + (0 if safe_dest else self._auto_safe_unlock_to_sorted_stack_score_k1) + dest_h * self._auto_safe_unlock_to_sorted_stack_score_k2 + (partial.H - partial.e(dest)) + source_bad)

    def update(self, partial, memory, action):
        if memory and memory[0] == action.so:
            return memory
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeUnlockToSortedStack()])
_AUTO = {'safe_unlock_to_sorted_stack_score_k1': 50000, 'safe_unlock_to_sorted_stack_score_k2': 10}
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
