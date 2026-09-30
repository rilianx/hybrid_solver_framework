from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_prefix_capping', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_gain': {'type': 'int', 'range': [0, 6], 'default': 0}, 'require_non_empty_dest': {'type': 'bool', 'default': False}, 'prefer_source_becomes_sorted': {'type': 'bool', 'default': True}, 'prefer_tighter_cap': {'type': 'bool', 'default': True}}}

class UnsortedToUnsortedPrefixCappingRule:
    name = 'unsorted_to_unsorted_prefix_capping'

    def __init__(self, min_dest_gain: int, require_non_empty_dest: bool, prefer_source_becomes_sorted: bool, prefer_larger_dest_gain: bool, prefer_tighter_cap: bool):
        self.min_dest_gain = int(min_dest_gain)
        self.require_non_empty_dest = bool(require_non_empty_dest)
        self.prefer_source_becomes_sorted = bool(prefer_source_becomes_sorted)
        self.prefer_larger_dest_gain = bool(prefer_larger_dest_gain)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)

    def _sorted_prefix_len(self, stack):
        if not stack:
            return 0
        n = 1
        for i in range(1, len(stack)):
            if stack[i - 1] >= stack[i]:
                n += 1
            else:
                break
        return n

    def _dest_old_prefix(self, partial, sd):
        if hasattr(partial, 'sorted_n'):
            return partial.sorted_n[sd]
        return self._sorted_prefix_len(partial.stacks[sd])

    def _dest_gain(self, partial, so, sd):
        src = partial.stacks[so]
        dst = partial.stacks[sd]
        moved = src[-1]
        old_prefix = self._dest_old_prefix(partial, sd)
        new_prefix = self._sorted_prefix_len(dst + [moved])
        return new_prefix - old_prefix

    def _source_after_prefix(self, partial, so):
        src = partial.stacks[so]
        if len(src) <= 1:
            return 0
        return self._sorted_prefix_len(src[:-1])

    def _fits_on_destination(self, partial, so, sd):
        if partial.h(sd) == 0:
            return True
        return partial.g(sd) >= partial.g(so)

    def _is_allowed_move(self, partial, action):
        so = action.so
        sd = action.sd
        if so == sd:
            return False
        if partial.h(so) == 0 or partial.e(sd) == 0:
            return False
        if partial.is_sorted_stack(so):
            return False
        if self.require_non_empty_dest and partial.h(sd) == 0:
            return False
        if partial.h(sd) > 0 and partial.is_sorted_stack(sd):
            return False
        if not self._fits_on_destination(partial, so, sd):
            return False
        return self._dest_gain(partial, so, sd) >= self.min_dest_gain

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd
        moved = partial.g(so)
        dest_gain = self._dest_gain(partial, so, sd)
        source_new_prefix = self._source_after_prefix(partial, so)
        source_becomes_sorted = source_new_prefix == partial.h(so) - 1
        cap_gap = 0 if partial.h(sd) == 0 else partial.g(sd) - moved
        dest_gain_rank = -dest_gain if self.prefer_larger_dest_gain else dest_gain
        source_sorted_rank = not source_becomes_sorted if self.prefer_source_becomes_sorted else source_becomes_sorted
        cap_rank = cap_gap if self.prefer_tighter_cap else -cap_gap
        return (dest_gain_rank, source_sorted_rank, cap_rank, -partial.h(sd), partial.h(so), so, sd)

    def allowed(self, partial, memory, candidates):
        moves = [a for a in candidates if self._is_allowed_move(partial, a)]
        moves.sort(key=lambda a: self._sort_key(partial, a))
        return moves

def build_component(problem, min_dest_gain=0, require_non_empty_dest=False, prefer_source_becomes_sorted=True, prefer_larger_dest_gain=True, prefer_tighter_cap=True):
    rule = UnsortedToUnsortedPrefixCappingRule(min_dest_gain=min_dest_gain, require_non_empty_dest=require_non_empty_dest, prefer_source_becomes_sorted=prefer_source_becomes_sorted, prefer_larger_dest_gain=prefer_larger_dest_gain, prefer_tighter_cap=prefer_tighter_cap)
    return RuleMachine(problem, [rule])
