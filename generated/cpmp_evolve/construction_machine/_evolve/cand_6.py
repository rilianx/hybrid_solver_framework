COMPONENT = {
    'name': 'safe_placement_refined_v5',
    'slot': 'construction_machine',
    'compatible_skeletons': ['CONSTRUCT'],
    'requires': [],
    'params': {},
}

from core.rules import RuleMachine


class SafePlacementRule:
    name = 'safe_placement'
    priority = 100

    def init(self, partial):
        return ()

    def _simulate(self, partial, action):
        nxt = partial.copy(track=False)
        nxt.move(action.so, action.sd)
        return nxt

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        current_bad = partial.bad()
        improving = []
        for action in candidates:
            nxt = self._simulate(partial, action)
            if nxt.bad() <= current_bad:
                improving.append(action)

        return improving if improving else list(candidates)

    def score(self, partial, memory, action):
        nxt = self._simulate(partial, action)

        base = (partial.S + 1) * (partial.H + 1) + 1

        source_sorted = 0 if not partial.is_sorted_stack(action.so) else 1
        dest_sorted = 0 if partial.is_sorted_stack(action.sd) else 1
        dest_empty = 0 if partial.h(action.sd) == 0 else 1

        bad_total = nxt.bad()
        unlocked_total = sum(nxt.ub(i) for i in range(nxt.S))
        sorted_piles = sum(1 for i in range(nxt.S) if nxt.is_sorted_stack(i))

        # Lexicographic encoding: smaller is better.
        score_int = 0
        for value in (
            bad_total,
            unlocked_total,
            dest_sorted,
            source_sorted,
            dest_empty,
            -sorted_piles,
            nxt.h(action.sd),
            action.so,
            action.sd,
        ):
            score_int = score_int * base + (value + 1000000)

        return float(score_int)


def build_component(problem, **params):
    return RuleMachine(problem, [SafePlacementRule()])
