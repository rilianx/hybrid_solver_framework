from core.rules import RuleMachine
COMPONENT = {'name': 'frontier_blocker_transfer', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_sorted_prefix': {'type': 'int', 'range': [0, 5], 'default': 1}, 'prefer_tighter_fit_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.1}}}

class FrontierBlockerTransfer:
    name = 'frontier_blocker_transfer'

    def __init__(self, single_bad_count, min_sorted_prefix, prefer_sorted_dest_bonus, prefer_long_prefix_weight, prefer_tighter_fit_weight):
        self.single_bad_count = int(single_bad_count)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.prefer_sorted_dest_bonus = float(prefer_sorted_dest_bonus)
        self.prefer_long_prefix_weight = float(prefer_long_prefix_weight)
        self.prefer_tighter_fit_weight = float(prefer_tighter_fit_weight)

    def _bad_count(self, partial, stack):
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_single_blocker_source(self, partial, stack):
        return partial.h(stack) > self.single_bad_count and self._bad_count(partial, stack) == self.single_bad_count and (partial.sorted_n[stack] >= self.min_sorted_prefix)

    def _is_sorted_receiving_dest(self, partial, stack, group):
        return partial.e(stack) > 0 and partial.is_sorted_stack(stack) and (partial.g(stack) >= group)

    def _is_single_blocker_frontier_dest(self, partial, stack, group):
        return partial.e(stack) > 0 and self._bad_count(partial, stack) == self.single_bad_count and (partial.sorted_n[stack] >= self.min_sorted_prefix) and (partial.g(stack) <= group)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._is_single_blocker_source(partial, so):
                continue
            moved_group = partial.g(so)
            if self._is_sorted_receiving_dest(partial, sd, moved_group) or self._is_single_blocker_frontier_dest(partial, sd, moved_group):
                allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        moved_group = partial.g(action.so)
        dst_top = partial.g(action.sd)
        dst_prefix = partial.sorted_n[action.sd]
        score = 0.0
        if partial.is_sorted_stack(action.sd) and dst_top >= moved_group:
            score -= self.prefer_sorted_dest_bonus
        score -= self.prefer_long_prefix_weight * float(dst_prefix)
        score += self.prefer_tighter_fit_weight * float(abs(dst_top - moved_group))
        return score

def build_component(problem, single_bad_count=1, min_sorted_prefix=1, prefer_sorted_dest_bonus=1.0, prefer_long_prefix_weight=1.0, prefer_tighter_fit_weight=0.1):
    rule = FrontierBlockerTransfer(single_bad_count=single_bad_count, min_sorted_prefix=min_sorted_prefix, prefer_sorted_dest_bonus=prefer_sorted_dest_bonus, prefer_long_prefix_weight=prefer_long_prefix_weight, prefer_tighter_fit_weight=prefer_tighter_fit_weight)
    return RuleMachine(problem, [rule])
