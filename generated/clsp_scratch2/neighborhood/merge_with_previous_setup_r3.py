from __future__ import annotations

from typing import Any, Iterable


COMPONENT = {
    "name": "merge_with_previous_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_lookback": {"type": "int", "range": [1, 6]},
        "min_savings_margin": {"type": "float", "range": [0.0, 1000.0]},
    },
}


class MergeWithPreviousSetupNeighborhood:
    """Neighborhood that shifts a setup to a previous setup when possible.

    Move format:
        (i, t, prev_t, prev_was_set)

    where a setup at period t is moved to period prev_t (typically the closest
    previous setup within the lookback window). The move is elementary and
    undoable exactly.
    """

    def __init__(self, problem: Any, max_lookback: int = 3, min_savings_margin: float = 0.0):
        self.problem = problem
        self.inst = problem.inst
        self.max_lookback = max_lookback
        self.min_savings_margin = min_savings_margin

    def _best_previous_setup(self, sol, i: int, t: int):
        start = max(0, t - self.max_lookback)
        for tt in range(t - 1, start - 1, -1):
            if sol[i][tt]:
                return tt
        return None

    def moves(self, sol) -> Iterable[tuple[int, int, int, bool]]:
        inst = self.inst
        n_items = inst.n_items
        n_periods = inst.n_periods

        for i in range(n_items):
            for t in range(1, n_periods):
                if not sol[i][t]:
                    continue

                prev_t = self._best_previous_setup(sol, i, t)
                if prev_t is None:
                    # Fallback to the immediately previous period to avoid an empty neighborhood
                    prev_t = t - 1

                if prev_t == t:
                    continue

                prev_was_set = bool(sol[i][prev_t])
                # Optional cheap filter based on demand/proxy savings; keep permissive to avoid emptiness.
                if inst.demand[i][t] <= self.min_savings_margin:
                    continue

                yield (i, t, prev_t, prev_was_set)

    def apply(self, sol, m):
        i, t, prev_t, prev_was_set = m
        s = [list(row) for row in sol]
        s[i][t] = False
        s[i][prev_t] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, prev_t, prev_was_set = m
        s = [list(row) for row in sol]
        s[i][t] = True
        s[i][prev_t] = prev_was_set
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_lookback: int = 3, min_savings_margin: float = 0.0):
    return MergeWithPreviousSetupNeighborhood(
        problem,
        max_lookback=max_lookback,
        min_savings_margin=min_savings_margin,
    )
