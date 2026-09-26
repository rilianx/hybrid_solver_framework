from __future__ import annotations

from typing import Any

COMPONENT = {
    "name": "capacity_fill_and_route_break_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "fill_weight": {"type": "float", "range": [0.0, 10.0]},
        "break_weight": {"type": "float", "range": [0.0, 20.0]},
        "demand_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class CapacityFillAndRouteBreakPenalty:
    """CVRP greedy score.

    Distinct idea:
    - Scores candidates mainly by how well they *fill the currently open route*,
      rather than by geometric continuation.
    - When a route is open, prefers customers whose demand leaves the least slack
      (or least overflow if a break is unavoidable).
    - When no route is open, prefers demands that are close to a robust target
      route load inferred from the remaining unassigned demand.
    """

    def __init__(
        self,
        problem,
        fill_weight: float = 1.0,
        break_weight: float = 2.0,
        demand_weight: float = 0.3,
    ):
        self.inst = problem.inst
        self.fill_weight = float(fill_weight)
        self.break_weight = float(break_weight)
        self.demand_weight = float(demand_weight)

        self._capacity = float(getattr(self.inst, "capacity"))
        self._demands = getattr(self.inst, "demand")

    def _current_load(self, partial: Any) -> float:
        current = getattr(partial, "current", None)
        if not current:
            return 0.0
        try:
            return float(sum(self._demands[int(c)] for c in current))
        except Exception:
            return 0.0

    def _remaining_demand(self, partial: Any) -> float:
        for attr in ("remaining", "unassigned", "unvisited", "pending"):
            rem = getattr(partial, attr, None)
            if rem is not None:
                try:
                    return float(sum(self._demands[int(c)] for c in rem))
                except Exception:
                    pass
        return 0.0

    def _target_load(self, partial: Any) -> float:
        cap = self._capacity
        if cap <= 0.0:
            return 0.0
        remaining = self._remaining_demand(partial)
        if remaining <= 0.0:
            return cap / 2.0
        # Target is the average load that could be packed into the remaining demand,
        # clipped to capacity. This is route-level and not distance-based.
        return min(cap, max(0.0, remaining % cap))

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        d = float(self._demands[c])
        cap = self._capacity
        load = self._current_load(partial)
        current = getattr(partial, "current", None)
        target = self._target_load(partial)

        if not current:
            # Starting a route: choose demands that are closest to the desired route load.
            gap = abs(d - target)
            norm = cap if cap > 0.0 else 1.0
            return float(self.fill_weight * (gap / norm) - self.demand_weight * (d / norm))

        next_load = load + d

        if next_load <= cap:
            # Prefer candidates that make the current route as close as possible to the target.
            slack_after = cap - next_load
            gap = abs(next_load - target)
            norm = cap if cap > 0.0 else 1.0
            return float(
                self.fill_weight * (gap / norm)
                + 0.5 * self.fill_weight * (slack_after / norm)
                - self.demand_weight * (d / norm)
            )

        # If the candidate would force a route break, penalize the overflow strongly.
        overflow = next_load - cap
        closeness_to_capacity = max(0.0, cap - load)
        norm = cap if cap > 0.0 else 1.0
        return float(
            self.break_weight * (overflow / norm)
            + 0.5 * self.fill_weight * (closeness_to_capacity / norm)
            - 0.25 * self.demand_weight * (d / norm)
        )


def build_component(problem, fill_weight: float = 1.0, break_weight: float = 2.0, demand_weight: float = 0.3):
    return CapacityFillAndRouteBreakPenalty(
        problem,
        fill_weight=fill_weight,
        break_weight=break_weight,
        demand_weight=demand_weight,
    )
