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
    """CVRP grand-tour construction heuristic.

    Idea:
    - Prefer customers whose demand is "urgent" with respect to the remaining
      capacity budget, so the tour order exposes useful split points.
    - Use depot-distance as a secondary signal, but not as the main driver.
    - This differs from nearest insertion because it ranks by future split
      pressure and demand frontiers rather than by immediate route extension cost.
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

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        inst = self.inst
        cap = float(inst.capacity)
        eps = 1e-9

        if kind == "close":
            # Closing is attractive when the current open route already carries
            # substantial load; this keeps future splits flexible.
            load = 0.0
            for c in open_route:
                load += float(inst.demand[c])
            fill = load / max(cap, eps)
            # Lower is better: prefer close only when the route is already full-ish.
            return 1.0 - self.load_weight * fill

        if kind != "add":
            return 0.0

        c = int(action[1])
        demand_c = float(inst.demand[c])

        current_load = 0.0
        for x in open_route:
            current_load += float(inst.demand[x])

        remaining_load = 0.0
        for x in remaining:
            remaining_load += float(inst.demand[x])

        # Frontier pressure: customers that consume a larger fraction of the
        # residual capacity are pushed earlier in the tour.
        residual_after = max(cap - (current_load + demand_c), 0.0)
        urgency = demand_c / max(cap - current_load, eps)

        # Balance term: favor keeping the open route near a meaningful fill level
        # so that split can later cut cleanly into feasible routes.
        target_fill = 0.75
        new_fill = (current_load + demand_c) / max(cap, eps)
        balance = abs(target_fill - new_fill)

        # Slack term: leaving too much unused capacity on the current frontier is
        # penalized, but only mildly.
        slack = residual_after / max(cap, eps)

        # Distances are still relevant, but only as a secondary tie-breaker.
        if not open_route:
            dist_term = float(inst.dist(0, c))
        else:
            last = open_route[-1]
            dist_term = float(inst.dist(last, c))

        # Additional demand-frontier term using the remaining pool: if the
        # customer is large relative to what is left overall, it should tend to
        # appear earlier so that the split decoder can place it into its own route
        # when necessary.
        if remaining_load > eps:
            relative_size = demand_c / remaining_load
        else:
            relative_size = 0.0

        return (
            self.load_weight * (balance + urgency + 0.5 * relative_size)
            - self.slack_weight * slack
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
