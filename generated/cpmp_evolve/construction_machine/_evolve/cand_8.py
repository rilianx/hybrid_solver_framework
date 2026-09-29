COMPONENT = {
    "name": "safe_placement_refined_v6_source_fix",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class SourceFixRule:
    name = "source_fix"
    priority = 110

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        chosen = []
        for action in candidates:
            so, sd = action.so, action.sd
            if partial.is_sorted_stack(so):
                continue

            tmp = partial.copy(track=False)
            tmp.move(so, sd)

            # Prefer moves that repair the source stack immediately.
            if tmp.is_sorted_stack(so):
                chosen.append(action)

        if not chosen:
            return []

        def key(action):
            so, sd = action.so, action.sd
            tmp = partial.copy(track=False)
            tmp.move(so, sd)
            return (
                tmp.bad(),
                0 if tmp.is_sorted_stack(sd) else 1,
                0 if tmp.is_sorted_stack(so) else 1,
                partial.ub(so),
                partial.ub(sd),
                so,
                sd,
            )

        return sorted(chosen, key=key)

    def update(self, partial, memory, action):
        return memory


class SafePlacementRule:
    name = "safe_placement"
    priority = 100

    def __init__(
        self,
        safe_placement_score_w_bad=1000000,
        safe_placement_score_w_source_sorted=1000,
        safe_placement_score_w_dest_unsorted=100,
        safe_placement_score_w_dest_nonempty=10,
        safe_placement_score_w_source_ub=1,
    ):
        self._auto_safe_placement_score_w_bad = safe_placement_score_w_bad
        self._auto_safe_placement_score_w_source_sorted = safe_placement_score_w_source_sorted
        self._auto_safe_placement_score_w_dest_unsorted = safe_placement_score_w_dest_unsorted
        self._auto_safe_placement_score_w_dest_nonempty = safe_placement_score_w_dest_nonempty
        self._auto_safe_placement_score_w_source_ub = safe_placement_score_w_source_ub

    def init(self, partial):
        return ()

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []
        return sorted(candidates, key=lambda a: self.score(partial, memory, a))

    def score(self, partial, memory, action):
        tmp = partial.copy(track=False)
        tmp.move(action.so, action.sd)
        after_bad = tmp.bad()
        source_sorted_after = 1 if tmp.is_sorted_stack(action.so) else 0
        dest_unsorted_after = 1 if not tmp.is_sorted_stack(action.sd) else 0
        dest_nonempty = 1 if partial.h(action.sd) > 0 else 0
        source_ub_after = tmp.ub(action.so)
        return float(
            after_bad * self._auto_safe_placement_score_w_bad
            + source_sorted_after * self._auto_safe_placement_score_w_source_sorted
            + dest_unsorted_after * self._auto_safe_placement_score_w_dest_unsorted
            + dest_nonempty * self._auto_safe_placement_score_w_dest_nonempty
            + source_ub_after * self._auto_safe_placement_score_w_source_ub
        )


def build_component(problem, **params):
    return RuleMachine(problem, [SourceFixRule(), SafePlacementRule(**params)])
