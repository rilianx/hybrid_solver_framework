COMPONENT = {'name': 'move_to_equal_top_destination_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class MoveToEqualTopDestinationRule:
    """Regla de construcción: prioriza movimientos cuyo destino tenga el mismo tope;
    si no existen, devuelve todos los movimientos factibles para no bloquear la construcción."""
    name = 'move_to_equal_top_destination_rule'

    def __init__(self, problem, prefer_nonempty_only=True):
        self.problem = problem
        self.prefer_nonempty_only = prefer_nonempty_only

    def allowed(self, partial, memory, candidates):
        feasible = []
        equal_top = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0:
                continue
            if partial.h(sd) >= partial.H:
                continue
            if self.prefer_nonempty_only and partial.h(sd) == 0:
                feasible.append(a)
                continue
            feasible.append(a)
            if partial.h(sd) > 0 and partial.g(so) == partial.g(sd):
                equal_top.append(a)
        if equal_top:
            return equal_top
        return feasible

def build_component(problem, **params):
    prefer_nonempty_only = params.get('prefer_nonempty_only', True)
    return RuleMachine(problem, [MoveToEqualTopDestinationRule(problem, prefer_nonempty_only=prefer_nonempty_only)])
