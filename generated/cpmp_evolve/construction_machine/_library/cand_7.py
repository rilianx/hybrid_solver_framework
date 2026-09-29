COMPONENT = {'name': 'safe_sorted_destination_rule_refine', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'lookahead_bonus': {'type': 'float', 'range': [0.0, 5.0], 'default': 1.0}, 'empty_stack_bonus': {'type': 'float', 'range': [0.0, 5.0], 'default': 0.8}, 'safe_sorted_destination_rule_refine_start_k1': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}, 'safe_sorted_destination_rule_refine_start_k2': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}, 'safe_sorted_destination_rule_refine_allowed_k4': {'type': 'float', 'range': [0.0, 0.1], 'default': 0.05}}}
from core.rules import RuleMachine

class RefinedSafeSortedDestinationRule:
    _auto_safe_sorted_destination_rule_refine_start_k1 = 0.01
    _auto_safe_sorted_destination_rule_refine_start_k2 = 0.01
    _auto_safe_sorted_destination_rule_refine_allowed_k1 = 0.5
    _auto_safe_sorted_destination_rule_refine_allowed_k2 = 0.25
    _auto_safe_sorted_destination_rule_refine_allowed_k3 = 0.2
    _auto_safe_sorted_destination_rule_refine_allowed_k4 = 0.05
    'Regla refinada: fija un destino prometedor y prioriza movimientos hacia pilas ordenadas o vacías.'
    name = 'safe_sorted_destination_rule_refine'

    def __init__(self, lookahead_bonus=1.0, empty_stack_bonus=0.8, strict_margin=1):
        self.lookahead_bonus = float(lookahead_bonus)
        self.empty_stack_bonus = float(empty_stack_bonus)
        self.strict_margin = int(strict_margin)

    def start(self, partial, memory):
        best_sd = None
        best_key = None
        for sd in range(partial.S):
            if partial.h(sd) >= partial.H:
                continue
            hsd = partial.h(sd)
            gsd = partial.g(sd)
            if hsd == 0:
                feasible = 1.0
                promise = self.empty_stack_bonus
            else:
                if not partial.is_sorted_stack(sd):
                    continue
                feasible = 1.0
                promise = max(0.0, float(partial.H - hsd)) * self._auto_safe_sorted_destination_rule_refine_start_k1
                if gsd < partial.G:
                    promise += max(0.0, float(partial.G - gsd)) * self.lookahead_bonus * self._auto_safe_sorted_destination_rule_refine_start_k2
            key = (-feasible, -promise, hsd, sd)
            if best_key is None or key < best_key:
                best_key = key
                best_sd = sd
        return {'sd': best_sd}

    def done(self, partial, memory):
        sd = memory.get('sd')
        if sd is None:
            return True
        if partial.h(sd) >= partial.H:
            return True
        if partial.h(sd) == 0:
            return False
        return not partial.is_sorted_stack(sd)

    def allowed(self, partial, memory, candidates):
        sd_fixed = memory.get('sd')
        allowed = []

        def move_score(a):
            so = a.so
            sd = a.sd
            src_top = partial.g(so)
            dst_h = partial.h(sd)
            dst_top = partial.g(sd) if dst_h > 0 else partial.G
            score = 0.0
            if dst_h == 0:
                score += self.empty_stack_bonus
            elif partial.is_sorted_stack(sd):
                score -= self._auto_safe_sorted_destination_rule_refine_allowed_k1 * self.lookahead_bonus
            if dst_h > 0 and dst_top >= src_top:
                score -= 1.0
            elif dst_h == 0:
                score -= self._auto_safe_sorted_destination_rule_refine_allowed_k2
            score += max(0, dst_h - (partial.H - self.strict_margin)) * self._auto_safe_sorted_destination_rule_refine_allowed_k3
            score -= float(partial.ub(so)) * self._auto_safe_sorted_destination_rule_refine_allowed_k4
            return score
        for a in candidates:
            if a.so == a.sd:
                continue
            if partial.h(a.so) <= 0:
                continue
            if partial.h(a.sd) >= partial.H:
                continue
            if sd_fixed is not None and a.sd != sd_fixed:
                continue
            src_group = partial.g(a.so)
            if src_group < 0:
                continue
            if partial.h(a.sd) == 0:
                allowed.append(a)
                continue
            if not partial.is_sorted_stack(a.sd):
                continue
            if partial.g(a.sd) >= src_group:
                allowed.append(a)
        if not allowed:
            return []
        allowed.sort(key=move_score)
        return allowed

def _build_component_llm(problem, **params):
    lookahead_bonus = params.get('lookahead_bonus', 1.0)
    empty_stack_bonus = params.get('empty_stack_bonus', 0.8)
    strict_margin = params.get('strict_margin', 1)
    rule = RefinedSafeSortedDestinationRule(lookahead_bonus=lookahead_bonus, empty_stack_bonus=empty_stack_bonus, strict_margin=strict_margin)
    return RuleMachine(problem, [rule])
_AUTO = {'safe_sorted_destination_rule_refine_start_k1': 0.01, 'safe_sorted_destination_rule_refine_start_k2': 0.01, 'safe_sorted_destination_rule_refine_allowed_k1': 0.5, 'safe_sorted_destination_rule_refine_allowed_k2': 0.25, 'safe_sorted_destination_rule_refine_allowed_k3': 0.2, 'safe_sorted_destination_rule_refine_allowed_k4': 0.05}
_AUTO_OWNER = {'safe_sorted_destination_rule_refine_start_k1': 'RefinedSafeSortedDestinationRule', 'safe_sorted_destination_rule_refine_start_k2': 'RefinedSafeSortedDestinationRule', 'safe_sorted_destination_rule_refine_allowed_k1': 'RefinedSafeSortedDestinationRule', 'safe_sorted_destination_rule_refine_allowed_k2': 'RefinedSafeSortedDestinationRule', 'safe_sorted_destination_rule_refine_allowed_k3': 'RefinedSafeSortedDestinationRule', 'safe_sorted_destination_rule_refine_allowed_k4': 'RefinedSafeSortedDestinationRule'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'RefinedSafeSortedDestinationRule': RefinedSafeSortedDestinationRule}
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
