COMPONENT = {'name': 'safe_unlock_to_sorted_stack_targeted_refined_rule_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'source_bad_weight': {'type': 'float', 'range': [0.0, 2000.0], 'default': 1000.0}, 'dest_free_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 10.0}, 'dest_top_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 1.0}, 'safe_unlock_to_sorted_stack_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
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

    def _action_key(self, partial, action):
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

    def start(self, partial, memory):
        candidates = []
        if hasattr(partial, 'visited') and partial.visited is not None:
            valid_actions = []
            for so in range(partial.S):
                if not partial.stacks[so]:
                    continue
                for sd in range(partial.S):
                    if not partial.valid(so, sd):
                        continue
                    if partial.after(so, sd) in partial.visited:
                        continue
                    valid_actions.append(type('A', (), {'so': so, 'sd': sd})())
        else:
            valid_actions = []
            for so in range(partial.S):
                if not partial.stacks[so]:
                    continue
                for sd in range(partial.S):
                    if partial.valid(so, sd):
                        valid_actions.append(type('A', (), {'so': so, 'sd': sd})())
        if not valid_actions:
            return (-1,)
        by_source = {}
        for act in valid_actions:
            by_source.setdefault(act.so, []).append(act)
        best_source = None
        best_key = None
        for so, acts in by_source.items():
            local_best = min(((self._action_key(partial, a), a.sd) for a in acts))
            key = (local_best[0], 0 if partial.sorted_n[so] < len(partial.stacks[so]) else 1, len(partial.stacks[so]) - partial.sorted_n[so], so)
            if best_key is None or key < best_key:
                best_key = key
                best_source = so
        return (best_source,)

    def done(self, partial, memory):
        return len(memory) == 1 and memory[0] == -1

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        if len(memory) != 1 or memory[0] == -1:
            return list(candidates)
        source = memory[0]
        allowed = [a for a in candidates if a.so == source]
        if allowed:
            return allowed
        return list(candidates)

    def score(self, partial, memory, action):
        return self._action_key(partial, action)

    def update(self, partial, memory, action):
        return ()

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
