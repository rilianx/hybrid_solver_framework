from math import ceil
from typing import Any


COMPONENT = {
    "name": "capacity_balance_frontier",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "load_weight": {"type": "float", "range": [0.0, 5.0]},
        "slack_weight": {"type": "float", "range": [0.0, 5.0]},
        "distance_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class CapacityBalanceFrontier:
    """Greedy score for CVRP grand-tour construction.

    Distinctive idea:
    - Score actions by how well they align the open prefix with an implied
      route-load quota derived from the remaining total demand.
    - This is a capacity-frontier heuristic: it tries to shape the tour so the
      Split decoder later finds balanced route boundaries.
    - Distance is only a tie-breaker / secondary signal.
    """

    def __init__(
        self,
        problem,
        load_weight: float = 1.0,
        slack_weight: float = 1.0,
        distance_weight: float = 0.5,
    ):
        self.inst = problem.inst
        self.load_weight = float(load_weight)
        self.slack_weight = float(slack_weight)
        self.distance_weight = float(distance_weight)

    def _load(self, nodes) -> float:
        inst = self.inst
        total = 0.0
        for c in nodes:
            total += float(inst.demand[c])
        return total

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        inst = self.inst
        cap = float(inst.capacity)
        eps = 1e-9

        current_load = self._load(open_route)
        remaining_load = self._load(remaining)

        # Minimal number of routes that will be needed for the not-yet-built mass,
        # plus the current open prefix if it were to be closed now.
        total_future = current_load + remaining_load
        min_routes_needed = max(1, int(ceil(total_future / max(cap, eps))))

        # Quota per route: the load we would like each split segment to carry
        # if the remaining customers were distributed as evenly as possible.
        target_route_load = total_future / min_routes_needed

        if kind == "close":
            # Closing is attractive when the current open prefix is close to the
            # implied target route load.
            fill_gap = abs(current_load - target_route_load) / max(cap, eps)
            # Also prefer closing when the prefix is already substantial.
            residual = max(cap - current_load, 0.0) / max(cap, eps)
            return self.load_weight * fill_gap + self.slack_weight * residual

        if kind != "add":
            return 0.0

        c = int(action[1])
        demand_c = float(inst.demand[c])
        new_load = current_load + demand_c

        # Core signal: how well the new prefix load matches the inferred quota.
        quota_gap = abs(new_load - target_route_load) / max(cap, eps)

        # Frontier signal: encourage using customers that reduce the difference
        # between the current prefix and the quota without overshooting too much.
        overshoot = max(new_load - target_route_load, 0.0) / max(cap, eps)

        # Slack signal: discourage leaving the prefix too empty relative to its quota.
        slack = max(target_route_load - new_load, 0.0) / max(cap, eps)

        # A weak balancing signal based on whether the customer is large relative
        # to the average remaining customer demand.
        if remaining:
            avg_remaining = remaining_load / float(len(remaining))
            demand_balance = abs(demand_c - avg_remaining) / max(cap, eps)
        else:
            demand_balance = 0.0

        # Distance is only secondary; this keeps the heuristic different from
        # nearest-insertion-style criteria.
        if not open_route:
            dist_term = float(inst.dist(0, c))
        else:
            dist_term = float(inst.dist(open_route[-1], c))

        return (
            self.load_weight * (quota_gap + 0.5 * overshoot + 0.25 * demand_balance)
            + self.slack_weight * slack
            + self.distance_weight * dist_term
        )


def build_component(
    problem,
    load_weight: float = 1.0,
    slack_weight: float = 1.0,
    distance_weight: float = 0.5,
):
    return CapacityBalanceFrontier(
        problem,
        load_weight=load_weight,
        slack_weight=slack_weight,
        distance_weight=distance_weight,
    )
