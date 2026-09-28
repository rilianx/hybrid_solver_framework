COMPONENT = {'name': 'repair_sorted_prefix', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'bad_reduction_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 4.0}, 'source_ub_penalty': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.5}, 'height_balance_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}}}
from core.machine import FALLBACK

class RepairSortedPrefixMachine:
    """Constructor greedy con un estado de reparación:
    prioriza movimientos que reducen contenedores mal puestos y apoyan pilas ya ordenadas.
    """
    states = ('repair',)

    def __init__(self, problem, bad_reduction_weight: float=4.0, destination_sorted_bonus: float=2.0, source_ub_penalty: float=1.5, height_balance_weight: float=0.5, transition_bad_threshold: int=0):
        self.problem = problem
        self._auto_bad_reduction_weight = bad_reduction_weight
        self._auto_destination_sorted_bonus = destination_sorted_bonus
        self._auto_source_ub_penalty = source_ub_penalty
        self._auto_height_balance_weight = height_balance_weight
        self._auto_transition_bad_threshold = transition_bad_threshold

    def initial(self, partial):
        return ('repair', ())

    def transition(self, partial, state, memory):
        if partial.is_sorted():
            return (FALLBACK, ())
        if partial.bad() <= self._auto_transition_bad_threshold and state == 'repair':
            return ('repair', ())
        return ('repair', ())

    def score(self, partial, state, memory, action):
        if state != 'repair':
            return 0.0
        so, sd = (action.so, action.sd)
        current_bad = partial.bad()
        current_src_ub = partial.ub(so)
        current_dst_sorted = partial.is_sorted_stack(sd)
        current_height_gap = abs(partial.h(so) - partial.h(sd))
        nxt = partial.copy()
        nxt.move(so, sd)
        bad_after = nxt.bad()
        bad_delta = bad_after - current_bad
        src_ub_after = nxt.ub(so)
        src_ub_delta = src_ub_after - current_src_ub
        dst_sorted_after = nxt.is_sorted_stack(sd)
        dst_sorted_gain = 1 if not current_dst_sorted and dst_sorted_after else 0
        height_gap_after = abs(nxt.h(so) - nxt.h(sd))
        height_gap_delta = height_gap_after - current_height_gap
        return self._auto_bad_reduction_weight * bad_delta + self._auto_source_ub_penalty * src_ub_delta - self._auto_destination_sorted_bonus * dst_sorted_gain + self._auto_height_balance_weight * height_gap_delta

    def update(self, partial, state, memory, action):
        return memory

def build_component(problem, **params):
    return RepairSortedPrefixMachine(problem, **params)
