COMPONENT = {'name': 'min_top_destination_rule', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}
from core.rules import RuleMachine

class MinTopDestinationRule:
    """Permite solo movimientos hacia el destino factible con menor tope."""
    name = 'min_top_destination_rule'

    def __init__(self, prefer_fuller_on_tie: bool=True, allow_empty_destination: bool=True):
        self.prefer_fuller_on_tie = prefer_fuller_on_tie
        self.allow_empty_destination = allow_empty_destination

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        def dest_key(a):
            sd = a.sd
            top = partial.g(sd)
            if partial.h(sd) == 0:
                top_key = float('inf') if not self.allow_empty_destination else partial.G + 1
            else:
                top_key = top
            if self.prefer_fuller_on_tie:
                tie_key = -partial.h(sd)
            else:
                tie_key = partial.h(sd)
            return (top_key, tie_key, sd)
        best = min(candidates, key=dest_key)
        best_key = dest_key(best)
        return [a for a in candidates if dest_key(a) == best_key]

def build_component(problem, **params):
    prefer_fuller_on_tie = params.get('prefer_fuller_on_tie', True)
    allow_empty_destination = params.get('allow_empty_destination', True)
    return RuleMachine(problem, [MinTopDestinationRule(prefer_fuller_on_tie=prefer_fuller_on_tie, allow_empty_destination=allow_empty_destination)])
