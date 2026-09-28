COMPONENT = {'name': 'repair_promote_safe_dest', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'safe_dest_bonus': {'type': 'float', 'range': [0.0, 5.0], 'default': 1.0}, 'sorted_dest_bonus': {'type': 'float', 'range': [0.0, 5.0], 'default': 2.0}, 'source_bad_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}, 'height_penalty': {'type': 'float', 'range': [0.0, 5.0], 'default': 1.0}}}
from core.machine import FALLBACK

class RepairPromoteSafeDest:
    """Un único estado para consolidar contenedores bien puestos en destinos seguros."""
    states = ('repair',)

    def __init__(self, problem, safe_dest_bonus: float=1.0, sorted_dest_bonus: float=2.0, source_bad_weight: float=1.0, height_penalty: float=1.0, visit_penalty: float=2.0):
        self.problem = problem
        self.safe_dest_bonus = safe_dest_bonus
        self.sorted_dest_bonus = sorted_dest_bonus
        self.source_bad_weight = source_bad_weight
        self.height_penalty = height_penalty
        self.visit_penalty = visit_penalty

    def initial(self, partial):
        return ('repair', ())

    def transition(self, partial, state, memory):
        if partial.is_sorted():
            return (FALLBACK, ())
        return ('repair', memory)

    def score(self, partial, state, memory, action):
        so, sd = (action.so, action.sd)
        c = partial.g(so)
        dest_top = partial.g(sd)
        dest_height = partial.h(sd)
        source_bad = partial.ub(so)
        dest_feasible = int(c <= dest_top)
        dest_safe = int(partial.is_sorted_stack(sd) and dest_feasible)
        next_hash = partial.after(so, sd)
        visited_pen = int(partial.visited is not None and next_hash in partial.visited)
        score = 0.0
        score += self.source_bad_weight * source_bad
        score += self.height_penalty * dest_height
        score -= self.safe_dest_bonus * dest_feasible
        score -= self.sorted_dest_bonus * dest_safe
        score += self.visit_penalty * visited_pen
        return score

    def update(self, partial, state, memory, action):
        return memory

def build_component(problem, **params):
    return RepairPromoteSafeDest(problem, safe_dest_bonus=params.get('safe_dest_bonus', 1.0), sorted_dest_bonus=params.get('sorted_dest_bonus', 2.0), source_bad_weight=params.get('source_bad_weight', 1.0), height_penalty=params.get('height_penalty', 1.0), visit_penalty=params.get('visit_penalty', 2.0))
