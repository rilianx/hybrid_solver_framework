COMPONENT = {'name': 'safe_relocate_greedy_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'bad_weight': {'type': 'float', 'range': [1.0, 5000000.0], 'default': 1000000.0}, 'unlock_weight': {'type': 'float', 'range': [0.0, 1000000.0], 'default': 10000.0}, 'dest_sorted_bonus': {'type': 'float', 'range': [0.0, 100000.0], 'default': 50.0}, 'dest_h_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 1.0}, 'source_h_weight': {'type': 'float', 'range': [0.0, 1000.0], 'default': 1.0}, 'source_g_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 0.1}, 'dest_g_weight': {'type': 'float', 'range': [0.0, 100.0], 'default': 0.01}, 'so_tiebreak': {'type': 'float', 'range': [0.0, 1.0], 'default': 0.0001}, 'sd_tiebreak': {'type': 'float', 'range': [0.0, 1.0], 'default': 1e-05}}}
from core.rules import RuleMachine

class SafeRelocateGreedy:
    name = 'safe_relocate_greedy'
    priority = 100

    def __init__(self, bad_weight: float=1000000.0, unlock_weight: float=10000.0, source_bad_weight: float=1000.0, source_ub_weight: float=100.0, dest_sorted_bonus: float=50.0, dest_ub_weight: float=10.0, dest_h_weight: float=1.0, source_h_weight: float=1.0, source_g_weight: float=0.1, dest_g_weight: float=0.01, so_tiebreak: float=0.0001, sd_tiebreak: float=1e-05):
        self.bad_weight = bad_weight
        self.unlock_weight = unlock_weight
        self.source_bad_weight = source_bad_weight
        self.source_ub_weight = source_ub_weight
        self.dest_sorted_bonus = dest_sorted_bonus
        self.dest_ub_weight = dest_ub_weight
        self.dest_h_weight = dest_h_weight
        self.source_h_weight = source_h_weight
        self.source_g_weight = source_g_weight
        self.dest_g_weight = dest_g_weight
        self.so_tiebreak = so_tiebreak
        self.sd_tiebreak = sd_tiebreak

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        return list(candidates)

    def score(self, partial, memory, action):
        so, sd = (action.so, action.sd)
        nxt = partial.copy(track=False)
        nxt.move(so, sd)
        new_bad = float(nxt.bad())
        unlocked = float(sum((nxt.ub(i) for i in range(nxt.S))))
        source_bad_after = float(nxt.h(so) - nxt.sorted_n[so])
        source_ub_after = float(nxt.ub(so))
        dest_ub_after = float(nxt.ub(sd))
        dest_sorted_after = 0.0 if nxt.is_sorted_stack(sd) else 1.0
        source_h = float(nxt.h(so))
        dest_h = float(nxt.h(sd))
        source_g = float(nxt.g(so))
        dest_g = float(nxt.g(sd))
        return self.bad_weight * new_bad + self.unlock_weight * unlocked + self.source_bad_weight * source_bad_after + self.source_ub_weight * source_ub_after + self.dest_sorted_bonus * dest_sorted_after + self.dest_ub_weight * dest_ub_after + self.source_h_weight * source_h + self.dest_h_weight * dest_h + self.source_g_weight * source_g + self.dest_g_weight * dest_g + self.so_tiebreak * float(so) + self.sd_tiebreak * float(sd)

    def update(self, partial, memory, action):
        return memory

def build_component(problem, **params):
    return RuleMachine(problem, [SafeRelocateGreedy(**params)])
