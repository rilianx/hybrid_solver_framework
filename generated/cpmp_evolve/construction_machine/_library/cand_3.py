COMPONENT = {'name': 'sorted_support_insert', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'sorted_support_insert_score_k1': {'type': 'float', 'range': [0.0, 0.2], 'default': 0.1}, 'sorted_support_insert_score_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.rules import RuleMachine

class SortedSupportInsert:
    _auto_sorted_support_insert_score_k1 = 0.1
    _auto_sorted_support_insert_score_k2 = 0.01
    'Regla de construcción: prioriza insertar contenedores en pilas ya ordenadas.'
    name = 'sorted_support_insert'
    priority = 80

    def allowed(self, partial, memory, candidates):
        allowed = []
        for a in candidates:
            so, sd = (a.so, a.sd)
            if not partial.is_sorted_stack(sd):
                continue
            if partial.g(so) <= partial.g(sd):
                allowed.append(a)
        return allowed

    def score(self, partial, memory, action):
        sd = action.sd
        so = action.so
        dest_height = float(partial.h(sd))
        src_height = float(partial.h(so))
        src_badness = float(partial.h(so) - partial.sorted_n[so])
        return dest_height + self._auto_sorted_support_insert_score_k1 * src_height - self._auto_sorted_support_insert_score_k2 * src_badness

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SortedSupportInsert()])

_AUTO = {'sorted_support_insert_score_k1': 0.1, 'sorted_support_insert_score_k2': 0.01}
_AUTO_OWNER = {'sorted_support_insert_score_k1': 'SortedSupportInsert', 'sorted_support_insert_score_k2': 'SortedSupportInsert'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SortedSupportInsert': SortedSupportInsert}
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
