from core.rules import RuleMachine

COMPONENT = {
    "name": "frontier_blocker_transfer_refined",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "single_bad_count": {"type": "int", "range": [1, 3], "default": 1},
        "min_sorted_prefix": {"type": "int", "range": [0, 5], "default": 1},
        "frontier_max_height": {"type": "int", "range": [1, 6], "default": 2},
        "allow_bad_suffix_receivers": {"type": "bool", "default": True},
        "prefer_sorted_source_bonus": {"type": "float", "range": [0.0, 20.0], "default": 8.0},
        "prefer_single_blocker_source_bonus": {"type": "float", "range": [0.0, 20.0], "default": 2.0},
        "prefer_safe_sorted_dest_bonus": {"type": "float", "range": [0.0, 20.0], "default": 3.0},
        "prefer_capped_dest_bonus": {"type": "float", "range": [0.0, 20.0], "default": 1.0},
        "prefer_short_source_weight": {"type": "float", "range": [0.0, 10.0], "default": 2.0},
        "prefer_long_dest_prefix_weight": {"type": "float", "range": [0.0, 10.0], "default": 1.0},
        "prefer_tighter_fit_weight": {"type": "float", "range": [0.0, 10.0], "default": 0.1},
    },
}


class FrontierBlockerTransferRefined:
    """Transfiere bloqueadores de frontera, priorizando fuentes cortas ordenadas o casi ordenadas."""

    name = "frontier_blocker_transfer"

    def __init__(
        self,
        single_bad_count,
        min_sorted_prefix,
        frontier_max_height,
        allow_bad_suffix_receivers,
        prefer_sorted_source_bonus,
        prefer_single_blocker_source_bonus,
        prefer_safe_sorted_dest_bonus,
        prefer_capped_dest_bonus,
        prefer_short_source_weight,
        prefer_long_dest_prefix_weight,
        prefer_tighter_fit_weight,
    ):
        self.single_bad_count = int(single_bad_count)
        self.min_sorted_prefix = int(min_sorted_prefix)
        self.frontier_max_height = int(frontier_max_height)
        self.allow_bad_suffix_receivers = bool(allow_bad_suffix_receivers)
        self.prefer_sorted_source_bonus = float(prefer_sorted_source_bonus)
        self.prefer_single_blocker_source_bonus = float(prefer_single_blocker_source_bonus)
        self.prefer_safe_sorted_dest_bonus = float(prefer_safe_sorted_dest_bonus)
        self.prefer_capped_dest_bonus = float(prefer_capped_dest_bonus)
        self.prefer_short_source_weight = float(prefer_short_source_weight)
        self.prefer_long_dest_prefix_weight = float(prefer_long_dest_prefix_weight)
        self.prefer_tighter_fit_weight = float(prefer_tighter_fit_weight)

    def _bad_count(self, partial, stack):
        return partial.h(stack) - partial.sorted_n[stack]

    def _is_sorted_frontier_source(self, partial, stack):
        return (
            partial.h(stack) > 0
            and partial.h(stack) <= self.frontier_max_height
            and partial.is_sorted_stack(stack)
            and partial.sorted_n[stack] >= self.min_sorted_prefix
        )

    def _is_single_blocker_source(self, partial, stack):
        return (
            partial.h(stack) > self.single_bad_count
            and self._bad_count(partial, stack) == self.single_bad_count
            and partial.sorted_n[stack] >= self.min_sorted_prefix
        )

    def _is_eligible_source(self, partial, stack):
        return self._is_sorted_frontier_source(partial, stack) or self._is_single_blocker_source(partial, stack)

    def _is_safe_sorted_dest(self, partial, stack, group):
        return partial.e(stack) > 0 and partial.is_sorted_stack(stack) and partial.g(stack) >= group

    def _is_capped_or_bad_suffix_dest(self, partial, stack, group):
        return (
            self.allow_bad_suffix_receivers
            and partial.e(stack) > 0
            and partial.sorted_n[stack] >= self.min_sorted_prefix
            and partial.g(stack) <= group
        )

    def _is_eligible_dest(self, partial, stack, group):
        return self._is_safe_sorted_dest(partial, stack, group) or self._is_capped_or_bad_suffix_dest(partial, stack, group)

    def allowed(self, partial, memory, candidates):
        allowed = []
        for action in candidates:
            so = action.so
            sd = action.sd
            if not self._is_eligible_source(partial, so):
                continue
            moved_group = partial.g(so)
            if self._is_eligible_dest(partial, sd, moved_group):
                allowed.append(action)
        return allowed

    def score(self, partial, memory, action):
        so = action.so
        sd = action.sd
        moved_group = partial.g(so)
        dst_top = partial.g(sd)
        dst_prefix = partial.sorted_n[sd]
        src_height = partial.h(so)

        score = 0.0

        if self._is_sorted_frontier_source(partial, so):
            score -= self.prefer_sorted_source_bonus
        elif self._is_single_blocker_source(partial, so):
            score -= self.prefer_single_blocker_source_bonus

        if self._is_safe_sorted_dest(partial, sd, moved_group):
            score -= self.prefer_safe_sorted_dest_bonus
        elif self._is_capped_or_bad_suffix_dest(partial, sd, moved_group):
            score -= self.prefer_capped_dest_bonus

        score += self.prefer_short_source_weight * float(src_height)
        score -= self.prefer_long_dest_prefix_weight * float(dst_prefix)
        score += self.prefer_tighter_fit_weight * float(abs(dst_top - moved_group))

        return score


def build_component(
    problem,
    single_bad_count=1,
    min_sorted_prefix=1,
    frontier_max_height=2,
    allow_bad_suffix_receivers=True,
    prefer_sorted_source_bonus=8.0,
    prefer_single_blocker_source_bonus=2.0,
    prefer_safe_sorted_dest_bonus=3.0,
    prefer_capped_dest_bonus=1.0,
    prefer_short_source_weight=2.0,
    prefer_long_dest_prefix_weight=1.0,
    prefer_tighter_fit_weight=0.1,
):
    rule = FrontierBlockerTransferRefined(
        single_bad_count=single_bad_count,
        min_sorted_prefix=min_sorted_prefix,
        frontier_max_height=frontier_max_height,
        allow_bad_suffix_receivers=allow_bad_suffix_receivers,
        prefer_sorted_source_bonus=prefer_sorted_source_bonus,
        prefer_single_blocker_source_bonus=prefer_single_blocker_source_bonus,
        prefer_safe_sorted_dest_bonus=prefer_safe_sorted_dest_bonus,
        prefer_capped_dest_bonus=prefer_capped_dest_bonus,
        prefer_short_source_weight=prefer_short_source_weight,
        prefer_long_dest_prefix_weight=prefer_long_dest_prefix_weight,
        prefer_tighter_fit_weight=prefer_tighter_fit_weight,
    )
    return RuleMachine(problem, [rule])
