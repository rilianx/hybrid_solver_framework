from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_top_to_empty_buffer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_bad_on_source': {'type': 'int', 'range': [1, 10], 'default': 2}, 'min_source_height': {'type': 'int', 'range': [1, 10], 'default': 2}, 'prefer_larger_top_group': {'type': 'bool', 'default': True}}}

class UnsortedTopToEmptyBuffer:
    _auto_unsorted_top_to_empty_buffer_score_k1 = 10.0
    'Move the top item of a disordered source stack to an empty destination stack.'
    name = 'unsorted_top_to_empty_buffer'

    def __init__(self, problem, min_bad_on_source=2, min_source_height=2, prefer_larger_top_group=True):
        self.problem = problem
        self.min_bad_on_source = int(min_bad_on_source)
        self.min_source_height = int(min_source_height)
        self.prefer_larger_top_group = bool(prefer_larger_top_group)

    def _is_applicable(self, partial, action):
        so = action.so
        sd = action.sd
        if so == sd:
            return False
        if partial.h(so) < self.min_source_height:
            return False
        if partial.h(sd) != 0:
            return False
        if partial.e(sd) <= 0:
            return False
        sorted_on_source = partial.sorted_n[so]
        height_on_source = partial.h(so)
        bad_on_source = height_on_source - sorted_on_source
        if bad_on_source < self.min_bad_on_source:
            return False
        if sorted_on_source >= height_on_source:
            return False
        if partial.visited is not None:
            nxt = partial.after(so, sd)
            if nxt in partial.visited:
                return False
        return True

    def _priority_tuple(self, partial, action):
        so = action.so
        sd = action.sd
        bad_on_source = partial.h(so) - partial.sorted_n[so]
        top_group = partial.g(so)
        if self.prefer_larger_top_group:
            group_key = -int(top_group)
        else:
            group_key = int(top_group)
        return (group_key, -int(bad_on_source), -int(partial.h(so)), int(sd), int(so))

    def allowed(self, partial, memory, candidates):
        allowed = [a for a in candidates if self._is_applicable(partial, a)]
        if not allowed:
            return []
        allowed.sort(key=lambda a: self._priority_tuple(partial, a))
        return allowed

    def score(self, partial, memory, action):
        pr = self._priority_tuple(partial, action)
        return float(pr[0] * 1000000000.0 + pr[1] * 1000000.0 + pr[2] * 1000.0 + pr[3] * self._auto_unsorted_top_to_empty_buffer_score_k1 + pr[4])

def _build_component_llm(problem, min_bad_on_source=2, min_source_height=2, prefer_larger_top_group=True, **params):
    rule = UnsortedTopToEmptyBuffer(problem=problem, min_bad_on_source=min_bad_on_source, min_source_height=min_source_height, prefer_larger_top_group=prefer_larger_top_group)
    return RuleMachine(problem, [rule])
_AUTO = {'unsorted_top_to_empty_buffer_score_k1': 10.0}
_AUTO_OWNER = {'unsorted_top_to_empty_buffer_score_k1': 'UnsortedTopToEmptyBuffer'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'UnsortedTopToEmptyBuffer': UnsortedTopToEmptyBuffer}
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
