from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_safe_bad_suffix_append', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_bad_in_source': {'type': 'int', 'range': [1, 10], 'default': 1}, 'min_bad_in_dest': {'type': 'int', 'range': [1, 10], 'default': 1}}}

class UnsortedToUnsortedSafeBadSuffixAppend:
    _auto_unsorted_to_unsorted_safe_bad_suffix_append_score_k1 = 0.01
    'Move from an unsorted source stack to an unsorted destination stack,\n    appending onto an already bad suffix without creating a new top inversion.\n    '
    name = 'unsorted_to_unsorted_safe_bad_suffix_append'

    def __init__(self, min_bad_in_source=1, min_bad_in_dest=1, prefer_emptying_source=True):
        self.min_bad_in_source = int(min_bad_in_source)
        self.min_bad_in_dest = int(min_bad_in_dest)
        self.prefer_emptying_source = bool(prefer_emptying_source)

    def _bad_count(self, layout, i):
        return layout.h(i) - layout.sorted_n[i]

    def _is_allowed_type(self, partial, action):
        so = action.so
        sd = action.sd
        if so == sd:
            return False
        if partial.h(so) == 0 or partial.e(sd) == 0:
            return False
        if partial.is_sorted_stack(so) or partial.is_sorted_stack(sd):
            return False
        bad_so = self._bad_count(partial, so)
        bad_sd = self._bad_count(partial, sd)
        if bad_so < self.min_bad_in_source or bad_sd < self.min_bad_in_dest:
            return False
        moved = partial.g(so)
        top_dest = partial.g(sd)
        return top_dest >= moved

    def allowed(self, partial, memory, candidates):
        allowed = [a for a in candidates if self._is_allowed_type(partial, a)]
        allowed.sort(key=lambda a: self.score(partial, memory, a))
        return allowed

    def score(self, partial, memory, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        top_dest = partial.g(sd)
        score = 0.0
        if self.prefer_emptying_source and partial.h(so) == 1:
            score -= 1000000.0
        score += float(top_dest - moved)
        score -= 1000.0 * float(self._bad_count(partial, sd))
        score += self._auto_unsorted_to_unsorted_safe_bad_suffix_append_score_k1 * float(partial.h(sd))
        score += 1e-06 * float(so)
        score += 1e-09 * float(sd)
        return score

def _build_component_llm(problem, min_bad_in_source=1, min_bad_in_dest=1, prefer_emptying_source=True, **params):
    return RuleMachine(problem, [UnsortedToUnsortedSafeBadSuffixAppend(min_bad_in_source=min_bad_in_source, min_bad_in_dest=min_bad_in_dest, prefer_emptying_source=prefer_emptying_source)])
_AUTO = {'unsorted_to_unsorted_safe_bad_suffix_append_score_k1': 0.01}
_AUTO_OWNER = {'unsorted_to_unsorted_safe_bad_suffix_append_score_k1': 'UnsortedToUnsortedSafeBadSuffixAppend'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'UnsortedToUnsortedSafeBadSuffixAppend': UnsortedToUnsortedSafeBadSuffixAppend}
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
