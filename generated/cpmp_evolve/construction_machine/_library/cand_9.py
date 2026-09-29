COMPONENT = {'name': 'move_good_top_to_bad_stack_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'max_badness_gap': {'type': 'int', 'range': [1, 20], 'default': 1}}}
from core.rules import RuleMachine

class MoveGoodTopToBadStack:
    """Mueve un tope bien puesto a una pila donde quedará mal puesto.

    La versión refinada restringe los destinos a los que lo dejan "apenas"
    mal puesto, para evitar decisiones demasiado agresivas cuando convienen
    otras piezas de la biblioteca.
    """
    name = 'move_good_top_to_bad_stack'

    def __init__(self, max_badness_gap: int=1, prefer_closest_bad_destination: bool=True):
        self.max_badness_gap = max_badness_gap
        self.prefer_closest_bad_destination = prefer_closest_bad_destination

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if partial.h(so) <= 0 or partial.h(sd) >= partial.H:
                continue
            moved = partial.g(so)
            if moved is None:
                continue
            if partial.h(so) > partial.sorted_n[so]:
                continue
            dest_top = partial.g(sd)
            if dest_top is None:
                continue
            if dest_top >= moved:
                continue
            gap = moved - dest_top
            if gap > self.max_badness_gap:
                continue
            allowed.append(a)
        if not allowed:
            return []
        if self.prefer_closest_bad_destination:
            allowed.sort(key=lambda a: (partial.g(a.so) - partial.g(a.sd), a.so, a.sd))
        return allowed

def build_component(problem, **params):
    max_badness_gap = params.get('max_badness_gap', 1)
    prefer_closest_bad_destination = params.get('prefer_closest_bad_destination', True)
    return RuleMachine(problem, [MoveGoodTopToBadStack(max_badness_gap=max_badness_gap, prefer_closest_bad_destination=prefer_closest_bad_destination)])
