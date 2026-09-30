COMPONENT = {
    "name": "adaptive_sorted_source_consolidation",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "min_source_height": {"type": "int", "range": [1, 10], "default": 1},
        "max_source_height": {"type": "int", "range": [1, 10], "default": 3},
        "max_source_bad_suffix": {"type": "int", "range": [0, 3], "default": 1},
        "min_exposed_sorted_prefix": {"type": "int", "range": [0, 10], "default": 1},
        "allow_unsorted_receivers": {"type": "bool", "default": True},
        "allow_sorted_receivers": {"type": "bool", "default": True},
        "allow_empty_receiver": {"type": "bool", "default": False},
        "prefer_safe_sorted_placement": {"type": "bool", "default": True},
        "prefer_near_sorted_peel": {"type": "bool", "default": True},
        "prefer_taller_receivers": {"type": "bool", "default": True},
    },
}

from core.rules import RuleMachine


class AdaptiveSortedSourceConsolidationRule:
    """Consolida pilas bajas usando fuentes ordenadas o casi ordenadas y receptores ordenados o con sufijo malo."""

    name = "sorted_source_consolidation"

    def __init__(
        self,
        min_source_height: int,
        max_source_height: int,
        max_source_bad_suffix: int,
        min_exposed_sorted_prefix: int,
        allow_unsorted_receivers: bool,
        allow_sorted_receivers: bool,
        allow_empty_receiver: bool,
        prefer_safe_sorted_placement: bool,
        prefer_near_sorted_peel: bool,
        prefer_taller_receivers: bool,
    ):
        self.min_source_height = min_source_height
        self.max_source_height = max_source_height
        self.max_source_bad_suffix = max_source_bad_suffix
        self.min_exposed_sorted_prefix = min_exposed_sorted_prefix
        self.allow_unsorted_receivers = allow_unsorted_receivers
        self.allow_sorted_receivers = allow_sorted_receivers
        self.allow_empty_receiver = allow_empty_receiver
        self.prefer_safe_sorted_placement = prefer_safe_sorted_placement
        self.prefer_near_sorted_peel = prefer_near_sorted_peel
        self.prefer_taller_receivers = prefer_taller_receivers

    def _source_profile(self, partial, so):
        height = partial.h(so)
        sorted_prefix = partial.sorted_n[so]
        bad_suffix = height - sorted_prefix
        is_sorted = partial.is_sorted_stack(so)
        is_near_sorted = (
            bad_suffix <= self.max_source_bad_suffix
            and sorted_prefix >= self.min_exposed_sorted_prefix
            and bad_suffix > 0
        )
        return height, sorted_prefix, bad_suffix, is_sorted, is_near_sorted

    def _receiver_ok(self, partial, action):
        dest_height = partial.h(action.sd)
        if dest_height == 0 and not self.allow_empty_receiver:
            return False

        dest_sorted = partial.is_sorted_stack(action.sd)
        if dest_sorted:
            return self.allow_sorted_receivers

        return self.allow_unsorted_receivers and partial.sorted_n[action.sd] < dest_height

    def _source_ok(self, partial, so):
        height, _, _, is_sorted, is_near_sorted = self._source_profile(partial, so)
        if height < self.min_source_height or height > self.max_source_height:
            return False
        return is_sorted or is_near_sorted

    def _sort_key(self, partial, action):
        so = action.so
        sd = action.sd

        source_height, source_sorted_prefix, source_bad_suffix, source_is_sorted, source_is_near_sorted = self._source_profile(partial, so)
        moved_group = partial.g(so)
        dest_height = partial.h(sd)
        dest_top = partial.g(sd)
        dest_is_sorted = partial.is_sorted_stack(sd)
        is_safe_sorted_placement = dest_is_sorted and moved_group <= dest_top
        frees_source = source_height == self.min_source_height
        exposes_sorted_source = source_bad_suffix > 0 and (source_height - source_bad_suffix) == source_sorted_prefix

        if self.prefer_safe_sorted_placement:
            safe_rank = not is_safe_sorted_placement
        else:
            safe_rank = is_safe_sorted_placement

        if self.prefer_near_sorted_peel:
            peel_rank = not source_is_near_sorted
        else:
            peel_rank = source_is_near_sorted

        receiver_rank = not dest_is_sorted
        free_rank = not frees_source
        expose_rank = not exposes_sorted_source

        receiver_height_rank = -dest_height if self.prefer_taller_receivers else dest_height

        return (
            safe_rank,
            peel_rank,
            receiver_rank,
            free_rank,
            expose_rank,
            source_height,
            moved_group,
            receiver_height_rank,
            so,
            sd,
        )

    def allowed(self, partial, memory, candidates):
        actions = []
        for action in candidates:
            if not self._source_ok(partial, action.so):
                continue
            if not self._receiver_ok(partial, action):
                continue
            actions.append(action)

        return sorted(actions, key=lambda action: self._sort_key(partial, action))


def build_component(
    problem,
    min_source_height=1,
    max_source_height=3,
    max_source_bad_suffix=1,
    min_exposed_sorted_prefix=1,
    allow_unsorted_receivers=True,
    allow_sorted_receivers=True,
    allow_empty_receiver=False,
    prefer_safe_sorted_placement=True,
    prefer_near_sorted_peel=True,
    prefer_taller_receivers=True,
    **params
):
    rule = AdaptiveSortedSourceConsolidationRule(
        min_source_height=min_source_height,
        max_source_height=max_source_height,
        max_source_bad_suffix=max_source_bad_suffix,
        min_exposed_sorted_prefix=min_exposed_sorted_prefix,
        allow_unsorted_receivers=allow_unsorted_receivers,
        allow_sorted_receivers=allow_sorted_receivers,
        allow_empty_receiver=allow_empty_receiver,
        prefer_safe_sorted_placement=prefer_safe_sorted_placement,
        prefer_near_sorted_peel=prefer_near_sorted_peel,
        prefer_taller_receivers=prefer_taller_receivers,
    )
    return RuleMachine(problem, [rule])
