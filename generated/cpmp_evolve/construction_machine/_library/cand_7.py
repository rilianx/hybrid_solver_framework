COMPONENT = {'name': 'repair_bad_top_move_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'repair_bad_top_move_allowed_k2': {'type': 'float', 'range': [0.0, 0.002], 'default': 0.001}}}
from core.rules import RuleMachine

class RepairBadTopMove:
    _auto_repair_bad_top_move_allowed_k1 = 0.01
    _auto_repair_bad_top_move_allowed_k2 = 0.001
    'Mueve un tope mal puesto, con foco macro sobre una pila objetivo si conviene.'
    name = 'repair_bad_top_move'

    def __init__(self, prefer_empty=True, prefer_lower_fill=True, bad_below_weight=2.5, sorted_source_penalty=1.5, same_height_bonus=0.5, switch_margin=1):
        self.prefer_empty = prefer_empty
        self.prefer_lower_fill = prefer_lower_fill
        self.bad_below_weight = bad_below_weight
        self.sorted_source_penalty = sorted_source_penalty
        self.same_height_bonus = same_height_bonus
        self.switch_margin = switch_margin

    def start(self, partial, memory):
        stacks = partial.stacks
        h = partial.h

        def is_bad_top_source(so):
            if h(so) <= 1:
                return False
            return stacks[so][-2] < stacks[so][-1]
        best = None
        best_key = None
        for so in range(partial.S):
            if not is_bad_top_source(so):
                continue
            top = stacks[so][-1]
            bad_below = partial.ub(so)
            src_sorted = partial.is_sorted_stack(so)
            key = (-bad_below, 0 if src_sorted else 1, -top, so)
            if best_key is None or key < best_key:
                best_key = key
                best = so
        return best

    def done(self, partial, memory):
        so = memory
        if so is None:
            return True
        if partial.h(so) <= 1:
            return True
        stacks = partial.stacks
        return stacks[so][-2] >= stacks[so][-1]

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        stacks = partial.stacks
        h = partial.h
        G = partial.G
        chosen_so = memory

        def is_bad_top_source(so):
            if h(so) <= 1:
                return False
            return stacks[so][-2] < stacks[so][-1]

        def top_group(i):
            return G if h(i) == 0 else stacks[i][-1]

        def dest_helps(moved, sd):
            if h(sd) == 0:
                return True
            return top_group(sd) >= moved
        filtered = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if h(so) == 0 or h(sd) >= partial.H:
                continue
            if not is_bad_top_source(so):
                continue
            if chosen_so is not None and so != chosen_so:
                continue
            moved = stacks[so][-1]
            if not dest_helps(moved, sd):
                continue
            filtered.append(a)
        if not filtered and chosen_so is not None:
            for a in candidates:
                so = a.so
                sd = a.sd
                if so == sd:
                    continue
                if h(so) == 0 or h(sd) >= partial.H:
                    continue
                if not is_bad_top_source(so):
                    continue
                moved = stacks[so][-1]
                if not dest_helps(moved, sd):
                    continue
                filtered.append(a)
        if not filtered:
            return []

        def key(a):
            so = a.so
            sd = a.sd
            moved = stacks[so][-1]
            src_bad_below = partial.ub(so)
            dest_fill = h(sd)
            dest_top = top_group(sd)
            src_sorted = partial.is_sorted_stack(so)
            score = 0.0
            score -= self.bad_below_weight * src_bad_below
            if src_sorted:
                score += self.sorted_source_penalty
            if self.prefer_empty:
                score += 0.0 if h(sd) == 0 else 1.0
            if self.prefer_lower_fill:
                score += dest_fill * self._auto_repair_bad_top_move_allowed_k1
            score += abs(dest_top - moved) * self._auto_repair_bad_top_move_allowed_k2
            score += sd * 1e-05
            score -= self.same_height_bonus if h(sd) == h(so) else 0.0
            return (score, -src_bad_below, dest_fill, sd)
        filtered.sort(key=key)
        return filtered

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [RepairBadTopMove(prefer_empty=params.get('prefer_empty', True), prefer_lower_fill=params.get('prefer_lower_fill', True), bad_below_weight=params.get('bad_below_weight', 2.5), sorted_source_penalty=params.get('sorted_source_penalty', 1.5), same_height_bonus=params.get('same_height_bonus', 0.5), switch_margin=params.get('switch_margin', 1))])
_AUTO = {'repair_bad_top_move_allowed_k1': 0.01, 'repair_bad_top_move_allowed_k2': 0.001}
_AUTO_OWNER = {'repair_bad_top_move_allowed_k1': 'RepairBadTopMove', 'repair_bad_top_move_allowed_k2': 'RepairBadTopMove'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'RepairBadTopMove': RepairBadTopMove}
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
