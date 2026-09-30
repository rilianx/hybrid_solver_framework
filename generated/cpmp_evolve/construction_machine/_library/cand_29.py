from core.rules import RuleMachine
COMPONENT = {'name': 'unsorted_to_unsorted_suffix_extension', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'min_dest_top_suffix': {'type': 'int', 'range': [1, 6], 'default': 1}, 'max_source_height': {'type': 'int', 'range': [1, 10], 'default': 10}, 'require_strict_unsorted_dest': {'type': 'bool', 'default': True}, 'prefer_longer_dest_suffix': {'type': 'bool', 'default': True}, 'prefer_tighter_cap': {'type': 'bool', 'default': True}}}

class UnsortedToUnsortedSuffixExtensionRule:
    """Permite mover desde una fuente desordenada a un destino desordenado cuando el tope movido extiende el sufijo ordenado superior del destino."""
    name = 'unsorted_to_unsorted_suffix_extension'

    def __init__(self, min_dest_top_suffix: int, max_source_height: int, require_strict_unsorted_dest: bool, prefer_longer_dest_suffix: bool, prefer_tighter_cap: bool, prefer_taller_dest: bool):
        self.min_dest_top_suffix = int(min_dest_top_suffix)
        self.max_source_height = int(max_source_height)
        self.require_strict_unsorted_dest = bool(require_strict_unsorted_dest)
        self.prefer_longer_dest_suffix = bool(prefer_longer_dest_suffix)
        self.prefer_tighter_cap = bool(prefer_tighter_cap)
        self.prefer_taller_dest = bool(prefer_taller_dest)

    def _top_sorted_suffix_len(self, partial, stack_idx: int) -> int:
        stack = partial.stacks[stack_idx]
        n = len(stack)
        if n == 0:
            return 0
        length = 1
        j = n - 1
        while j > 0 and stack[j - 1] >= stack[j]:
            length += 1
            j -= 1
        return length

    def _is_unsorted_source(self, partial, so: int) -> bool:
        return 0 < partial.h(so) <= self.max_source_height and (not partial.is_sorted_stack(so))

    def _is_eligible_unsorted_dest(self, partial, sd: int) -> bool:
        if partial.e(sd) <= 0 or partial.h(sd) == 0:
            return False
        if self.require_strict_unsorted_dest and partial.is_sorted_stack(sd):
            return False
        suffix_len = self._top_sorted_suffix_len(partial, sd)
        return suffix_len >= self.min_dest_top_suffix

    def _extends_dest_suffix(self, partial, so: int, sd: int) -> bool:
        moved = partial.g(so)
        dest_top = partial.g(sd)
        return moved <= dest_top

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if so == sd:
                continue
            if not self._is_unsorted_source(partial, so):
                continue
            if not self._is_eligible_unsorted_dest(partial, sd):
                continue
            if not self._extends_dest_suffix(partial, so, sd):
                continue
            allowed.append(action)

        def key(action):
            so = action.so
            sd = action.sd
            moved = partial.g(so)
            dest_top = partial.g(sd)
            suffix_len = self._top_sorted_suffix_len(partial, sd)
            tight_gap = dest_top - moved
            dest_height = partial.h(sd)
            suffix_rank = -suffix_len if self.prefer_longer_dest_suffix else suffix_len
            gap_rank = tight_gap if self.prefer_tighter_cap else -tight_gap
            dest_rank = -dest_height if self.prefer_taller_dest else dest_height
            return (suffix_rank, gap_rank, dest_rank, partial.h(so), so, sd)
        allowed.sort(key=key)
        return allowed

def build_component(problem, min_dest_top_suffix=1, max_source_height=10, require_strict_unsorted_dest=True, prefer_longer_dest_suffix=True, prefer_tighter_cap=True, prefer_taller_dest=True):
    rule = UnsortedToUnsortedSuffixExtensionRule(min_dest_top_suffix=min_dest_top_suffix, max_source_height=max_source_height, require_strict_unsorted_dest=require_strict_unsorted_dest, prefer_longer_dest_suffix=prefer_longer_dest_suffix, prefer_tighter_cap=prefer_tighter_cap, prefer_taller_dest=prefer_taller_dest)
    return RuleMachine(problem, [rule])
