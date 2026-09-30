from core.rules import RuleMachine
COMPONENT = {'name': 'sorted_release_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_empty_stacks': {'type': 'int', 'range': [1, 3], 'default': 1}}}

class SortedReleaseToEmptyBufferRule:
    _auto_sorted_release_to_empty_buffer_score_k1 = 0.001
    name = 'sorted_release_to_empty_buffer'

    def __init__(self, max_source_height: int=2, max_remaining_height: int=1, min_empty_stacks: int=1):
        self.max_source_height = int(max_source_height)
        self.max_remaining_height = int(max_remaining_height)
        self.min_empty_stacks = int(min_empty_stacks)

    def _empty_stacks(self, partial) -> int:
        return sum((1 for i in range(partial.S) if partial.h(i) == 0))

    def _is_allowed_type(self, partial, action) -> bool:
        so = action.so
        sd = action.sd
        hs = partial.h(so)
        if hs <= 0:
            return False
        if hs > self.max_source_height:
            return False
        if not partial.is_sorted_stack(so):
            return False
        if partial.h(sd) != 0:
            return False
        remaining = hs - 1
        if remaining > self.max_remaining_height:
            return False
        if self._empty_stacks(partial) < self.min_empty_stacks:
            return False
        if partial.visited is not None:
            nxt = partial.after(so, sd)
            if nxt in partial.visited:
                return False
        return True

    def allowed(self, partial, memory, candidates):
        moves = [a for a in candidates if self._is_allowed_type(partial, a)]
        moves.sort(key=lambda a: self.score(partial, memory, a))
        return moves

    def score(self, partial, memory, action) -> float:
        so = action.so
        sd = action.sd
        remaining = partial.h(so) - 1
        top_group = partial.g(so)
        return float(remaining) * 1000000.0 - float(top_group) * 1000.0 + float(so) * 1.0 + float(sd) * self._auto_sorted_release_to_empty_buffer_score_k1

def _build_component_llm(problem, **params):
    rule = SortedReleaseToEmptyBufferRule(max_source_height=params.get('max_source_height', 2), max_remaining_height=params.get('max_remaining_height', 1), min_empty_stacks=params.get('min_empty_stacks', 1))
    return RuleMachine(problem, [rule])
_AUTO = {'sorted_release_to_empty_buffer_score_k1': 0.001}
_AUTO_OWNER = {'sorted_release_to_empty_buffer_score_k1': 'SortedReleaseToEmptyBufferRule'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SortedReleaseToEmptyBufferRule': SortedReleaseToEmptyBufferRule}
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
