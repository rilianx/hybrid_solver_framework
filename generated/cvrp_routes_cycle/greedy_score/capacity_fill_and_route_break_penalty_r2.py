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

    Heuristic idea:
    - Uses the *current route load* and, if available, the remaining unassigned demand
      to favor actions that make the currently open route structurally efficient.
    - Rewards actions that bring the current route closer to being tightly packed.
    - Penalizes actions that force a route break when the open route is still far from full.
    - Slightly prefers larger-demand customers when they help close the current route.

    Lower score is better.
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
        demands = getattr(self.inst, "demand")
        self._demands = demands

    def _current_load(self, partial: Any) -> float:
        current = getattr(partial, "current", None)
        if not current:
            return 0.0
        return float(sum(self._demands[int(c)] for c in current))

    def _remaining_demand(self, partial: Any) -> float:
        for attr in ("remaining", "unassigned", "unvisited", "pending"):
            rem = getattr(partial, attr, None)
            if rem is not None:
                try:
                    return float(sum(self._demands[int(c)] for c in rem))
                except Exception:
                    pass
        return 0.0

    def score(self, partial: Any, action: Any) -> float:
        c = int(action)
        d = float(self._demands[c])
        cap = self._capacity
        load = self._current_load(partial)
        current = getattr(partial, "current", None)

        # Baseline: prefer using customers that help create fuller routes overall.
        remaining_demand = self._remaining_demand(partial)
        if remaining_demand > 0.0 and cap > 0.0:
            # A rough route-completion target: how much load would be "natural" to pack now.
            target_fill = min(cap, max(0.0, remaining_demand % cap))
        else:
            target_fill = cap / 2.0 if cap > 0.0 else 0.0

        if not current:
            # Starting a route: prefer customers whose demand makes the first route
            # closer to the target fill, rather than nearest-neighbor continuation.
            gap = abs(d - target_fill)
            return float(self.fill_weight * (gap / cap if cap > 0.0 else gap) - self.demand_weight * d)

        next_load = load + d

        if next_load <= cap:
            slack = cap - next_load
            # Prefer actions that reduce remaining slack toward the target fill.
            gap = abs(next_load - target_fill)
            fill_penalty = gap / cap if cap > 0.0 else gap
            slack_penalty = slack / cap if cap > 0.0 else slack
            return float(
                self.fill_weight * fill_penalty
                + 0.5 * self.fill_weight * slack_penalty
                - self.demand_weight * d
            )

        # Route break is forced: penalize the overflow, but also prefer larger demands
        # only when they are the reason the current route is nearly complete.
        overflow = next_load - cap
        closeness_to_full = max(0.0, cap - load) / cap if cap > 0.0 else max(0.0, cap - load)
        break_penalty = overflow / cap if cap > 0.0 else overflow

        # If the route is already close to full, breaking it is less harmful.
        return float(
            self.break_weight * break_penalty
            + 0.5 * self.fill_weight * closeness_to_full
            - self.demand_weight * d
        )


def build_component(problem, fill_weight: float = 1.0, break_weight: float = 2.0, demand_weight: float = 0.3):
    return CapacityFillAndRouteBreakPenalty(
        problem,
        fill_weight=fill_weight,
        break_weight=break_weight,
        demand_weight=demand_weight,
    )
