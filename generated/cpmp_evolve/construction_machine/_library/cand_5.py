COMPONENT = {'name': 'safe_sorted_destination_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'allow_empty_escape': {'type': 'bool', 'default': True, 'values': [True, False]}, 'prefer_lower_top': {'type': 'bool', 'default': True, 'values': [True, False]}}}
from core.rules import RuleMachine

class SafeSortedDestinationRule:
    _auto_safe_sorted_destination_rule_key_k1 = 3
    'Permite movimientos hacia destinos seguros, priorizando pilas ordenadas y con mejor holgura.'
    name = 'safe_sorted_destination_rule'

    def __init__(self, prefer_nonempty: bool=True, allow_empty_escape: bool=True, prefer_lower_top: bool=True, prefer_more_slack: bool=True, macro_mode: bool=False):
        self.prefer_nonempty = prefer_nonempty
        self.allow_empty_escape = allow_empty_escape
        self.prefer_lower_top = prefer_lower_top
        self.prefer_more_slack = prefer_more_slack
        self.macro_mode = macro_mode

    def start(self, partial, memory):
        if not self.macro_mode:
            return memory
        return {'bad0': partial.bad(), 'sorted0': partial.is_sorted()}

    def done(self, partial, memory):
        if not self.macro_mode:
            return False
        return partial.is_sorted() or partial.bad() >= memory.get('bad0', partial.bad())

    def _key(self, partial, action):
        so = action.so
        sd = action.sd
        dest_h = partial.h(sd)
        dest_top = partial.g(sd)
        src_top = partial.g(so)
        src_ub = partial.ub(so)
        safe_dest = 0
        if dest_h == 0:
            safe_dest = 2
        elif partial.is_sorted_stack(sd) and dest_top >= src_top:
            safe_dest = 0
        elif partial.is_sorted_stack(sd):
            safe_dest = 1
        else:
            safe_dest = self._auto_safe_sorted_destination_rule_key_k1
        top_key = dest_top if self.prefer_lower_top else -dest_top
        slack_key = -partial.e(sd) if self.prefer_more_slack else partial.e(sd)
        empty_key = 0 if dest_h > 0 else 1 if self.allow_empty_escape else 2
        nonempty_pref = 0 if not self.prefer_nonempty or dest_h > 0 else 1
        src_key = -src_ub
        return (safe_dest, empty_key, nonempty_pref, top_key, slack_key, src_key, sd)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0:
                continue
            if partial.h(sd) >= partial.H:
                continue
            src_group = partial.g(so)
            if src_group < 0:
                continue
            dest_h = partial.h(sd)
            ok = False
            if dest_h == 0:
                ok = self.allow_empty_escape
            elif partial.is_sorted_stack(sd):
                ok = partial.g(sd) >= src_group
            else:
                ok = partial.g(sd) >= src_group and partial.ub(sd) == 0
            if not ok:
                continue
            allowed.append(a)
        allowed.sort(key=lambda a: self._key(partial, a))
        if self.macro_mode and memory is not None:
            memory['last_allowed'] = len(allowed)
        return allowed

def _build_component_llm(problem, **params):
    return RuleMachine(problem, [SafeSortedDestinationRule(prefer_nonempty=params.get('prefer_nonempty', True), allow_empty_escape=params.get('allow_empty_escape', True), prefer_lower_top=params.get('prefer_lower_top', True), prefer_more_slack=params.get('prefer_more_slack', True), macro_mode=params.get('macro_mode', False))])
_AUTO = {'safe_sorted_destination_rule_key_k1': 3}
_AUTO_OWNER = {'safe_sorted_destination_rule_key_k1': 'SafeSortedDestinationRule'}
_AUTO_ATTR = {}
_AUTO_CLASSES = {'SafeSortedDestinationRule': SafeSortedDestinationRule}
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
