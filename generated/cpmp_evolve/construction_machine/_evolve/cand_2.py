COMPONENT = {'name': 'safe_placement_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_placement_score_k1': {'type': 'int', 'range': [0, 4294967294], 'default': 2147483647}}}
from core.rules import RuleMachine

class SafePlacementRule:
    _auto_safe_placement_score_k1 = 2147483647
    name = 'safe_placement'
    priority = 100

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        def compatible(action):
            return partial.h(action.sd) == 0 or partial.g(action.sd) >= partial.g(action.so)
        compatible_candidates = [a for a in candidates if compatible(a)]
        if not compatible_candidates:
            return []
        sorted_compatible = [a for a in compatible_candidates if partial.is_sorted_stack(a.sd)]
        if sorted_compatible:
            return sorted(sorted_compatible, key=lambda a: (partial.h(a.sd), 0 if partial.is_sorted_stack(a.so) else 1, partial.g(a.sd), a.so, a.sd))
        non_empty_compatible = [a for a in compatible_candidates if partial.h(a.sd) > 0]
        if non_empty_compatible:
            return sorted(non_empty_compatible, key=lambda a: (partial.g(a.sd), partial.h(a.sd), 0 if partial.is_sorted_stack(a.so) else 1, a.so, a.sd))
        return sorted(compatible_candidates, key=lambda a: (partial.h(a.sd), 0 if partial.is_sorted_stack(a.so) else 1, a.so, a.sd))

    def score(self, partial, memory, action):
        dest_top = partial.g(action.sd)
        source_top = partial.g(action.so)
        dest_empty = 1 if partial.h(action.sd) == 0 else 0
        return float((0 if partial.is_sorted_stack(action.sd) else 1, 0 if not partial.is_sorted_stack(action.so) else 1, 1 if dest_empty else 0, dest_top, -source_top, action.so, action.sd).__hash__() & self._auto_safe_placement_score_k1)

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafePlacementRule()])

_AUTO = {'safe_placement_score_k1': 2147483647}
_AUTO_OWNER = {'safe_placement_score_k1': 'SafePlacementRule'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafePlacementRule': SafePlacementRule}
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
