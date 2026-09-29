COMPONENT = {'name': 'unlock_to_sorted_support', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class UnlockToSortedSupport:
    _auto_unlock_to_sorted_support_score_k1 = 10
    'Mueve un contenedor bloqueado a una pila ya ordenada que lo pueda soportar.'
    name = 'unlock_to_sorted_support'
    priority = 100

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        allowed = []
        for a in candidates:
            so, sd = (a.so, a.sd)
            if partial.ub(so) <= 0:
                continue
            if not partial.is_sorted_stack(sd):
                continue
            if partial.g(sd) < partial.g(so):
                continue
            allowed.append(a)
        return allowed

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy(track=False)
        before_bad = nxt.bad()
        before_src_ub = nxt.ub(so)
        before_dst_h = nxt.h(sd)
        nxt.move(so, sd)
        after_bad = nxt.bad()
        after_src_ub = nxt.ub(so) if so < nxt.S else 0
        after_dst_sorted = 1 if nxt.is_sorted_stack(sd) else 0
        return 1000000 * after_bad - 10000 * (before_bad - after_bad) - 1000 * (before_src_ub - after_src_ub) - 100 * after_dst_sorted + self._auto_unlock_to_sorted_support_score_k1 * before_dst_h + sd

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [UnlockToSortedSupport()])
_AUTO = {'unlock_to_sorted_support_score_k1': 10}
_AUTO_OWNER = {'unlock_to_sorted_support_score_k1': 'UnlockToSortedSupport'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'UnlockToSortedSupport': UnlockToSortedSupport}
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
