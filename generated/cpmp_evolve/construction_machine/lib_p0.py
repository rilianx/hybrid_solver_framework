COMPONENT = {'name': 'safe_relocate_greedy', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_relocate_greedy_score_k2': {'type': 'float', 'range': [0.0, 0.2], 'default': 0.1}, 'safe_relocate_greedy_score_k3': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}
from core.rules import RuleMachine

class SafeRelocateGreedy:
    _auto_safe_relocate_greedy_score_k1 = 10.0
    _auto_safe_relocate_greedy_score_k2 = 0.1
    _auto_safe_relocate_greedy_score_k3 = 0.01
    _auto_safe_relocate_greedy_score_k4 = 0.001
    'Regla simple: prioriza recolocaciones que reduzcan la cota local de malos puestos.'
    name = 'safe_relocate_greedy'
    priority = 100

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        return list(candidates)

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy(track=False)
        nxt.move(so, sd)
        new_bad = float(nxt.bad())
        new_ub = float(sum((nxt.ub(i) for i in range(nxt.S))))
        source_ub = float(partial.ub(so))
        source_h = float(partial.h(so))
        dest_h = float(partial.h(sd))
        dest_g = float(partial.g(sd))
        source_g = float(partial.g(so))
        c = float(partial.g(so))
        dest_well_placed = 0.0 if partial.h(sd) == 0 or c <= dest_g else 1.0
        return 1000000.0 * new_bad + 10000.0 * new_ub + 100.0 * dest_well_placed + self._auto_safe_relocate_greedy_score_k1 * source_ub + 1.0 * source_h + self._auto_safe_relocate_greedy_score_k2 * dest_h + self._auto_safe_relocate_greedy_score_k3 * source_g + self._auto_safe_relocate_greedy_score_k4 * dest_g + 0.0001 * float(so) + 1e-05 * float(sd)

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeRelocateGreedy()])
_AUTO = {'safe_relocate_greedy_score_k1': 10.0, 'safe_relocate_greedy_score_k2': 0.1, 'safe_relocate_greedy_score_k3': 0.01, 'safe_relocate_greedy_score_k4': 0.001}
_AUTO_OWNER = {'safe_relocate_greedy_score_k1': 'SafeRelocateGreedy', 'safe_relocate_greedy_score_k2': 'SafeRelocateGreedy', 'safe_relocate_greedy_score_k3': 'SafeRelocateGreedy', 'safe_relocate_greedy_score_k4': 'SafeRelocateGreedy'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeRelocateGreedy': SafeRelocateGreedy}
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
