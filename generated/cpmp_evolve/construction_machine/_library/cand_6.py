COMPONENT = {'name': 'safe_relocate_greedy_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_insert_bonus': {'type': 'float', 'range': [0.0, 1.0], 'default': 0.35}, 'source_ub_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.5}, 'dest_height_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.2}, 'dest_slack_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.1}, 'safe_relocate_greedy_score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}}}
from core.rules import RuleMachine

class SafeRelocateGreedy:
    _auto_safe_relocate_greedy_score_k1 = 10.0
    name = 'safe_relocate_greedy'
    priority = 100

    def __init__(self, safe_insert_bonus: float=0.35, source_bad_weight: float=2.5, source_ub_weight: float=1.5, dest_height_weight: float=0.2, dest_slack_weight: float=0.1):
        self.safe_insert_bonus = float(safe_insert_bonus)
        self.source_bad_weight = float(source_bad_weight)
        self.source_ub_weight = float(source_ub_weight)
        self.dest_height_weight = float(dest_height_weight)
        self.dest_slack_weight = float(dest_slack_weight)

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        preferred = []
        secondary = []
        fallback = []
        for a in candidates:
            so, sd = (a.so, a.sd)
            c = partial.g(so)
            dest_top = partial.g(sd)
            dest_sorted = partial.is_sorted_stack(sd)
            if dest_sorted and c <= dest_top:
                preferred.append(a)
                continue
            if c <= dest_top or partial.ub(so) > 0:
                secondary.append(a)
            else:
                fallback.append(a)
        if preferred:
            return sorted(preferred, key=lambda a: self.score(partial, memory, a))
        if secondary:
            return sorted(secondary, key=lambda a: self.score(partial, memory, a))
        return sorted(fallback, key=lambda a: self.score(partial, memory, a))

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy(track=False)
        nxt.move(so, sd)
        new_bad = float(nxt.bad())
        source_bad = float(partial.bad())
        source_ub = float(partial.ub(so))
        dest_ub = float(partial.ub(sd))
        dest_h = float(partial.h(sd))
        dest_e = float(partial.e(sd))
        source_h = float(partial.h(so))
        c = float(partial.g(so))
        dest_top = float(partial.g(sd))
        safe_insert = 1.0 if c <= dest_top else 0.0
        dest_sorted = 1.0 if partial.is_sorted_stack(sd) else 0.0
        score = 1000000.0 * new_bad
        score += self.source_bad_weight * source_bad
        score += self.source_ub_weight * source_ub
        score += self.dest_height_weight * dest_h
        score += self.dest_slack_weight * dest_e
        score -= self.safe_insert_bonus * (100.0 * dest_sorted + self._auto_safe_relocate_greedy_score_k1 * safe_insert)
        score += 0.0001 * float(so) + 1e-05 * float(sd) + 1e-06 * dest_ub + 1e-07 * source_h
        return score

    def update(self, partial, memory, action):
        return memory

def _build_component_llm(problem, **params):
    rule = SafeRelocateGreedy(safe_insert_bonus=params.get('safe_insert_bonus', 0.35), source_bad_weight=params.get('source_bad_weight', 2.5), source_ub_weight=params.get('source_ub_weight', 1.5), dest_height_weight=params.get('dest_height_weight', 0.2), dest_slack_weight=params.get('dest_slack_weight', 0.1))
    return RuleMachine(problem, [rule])
_AUTO = {'safe_relocate_greedy_score_k1': 10.0}
_AUTO_OWNER = {'safe_relocate_greedy_score_k1': 'SafeRelocateGreedy'}
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
