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
    - Prefer actions that keep the current route load balanced.
    - Reward using capacity efficiently, but avoid packing routes too tightly too early.
    - This is structurally different from pure nearest insertion: it is primarily a
      load-management heuristic with distance as a secondary signal.
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

        if kind == "close":
            # Closing becomes more attractive when the current open route load is
            # already substantial, to avoid over-committing to a route.
            load = sum(float(inst.demand[c]) for c in open_route)
            fill = load / max(cap, 1e-9)
            return 1.0 - self.load_weight * fill

        if kind != "add":
            return 0.0

        c = int(action[1])
        demand = float(inst.demand[c])

        current_load = sum(float(inst.demand[x]) for x in open_route)
        new_load = current_load + demand

        # Balance term: prefer loads near half capacity for the current route.
        balance = abs(0.5 * cap - new_load) / max(cap, 1e-9)

        # Slack term: keep some remaining room for the next customers.
        slack = max(0.0, cap - new_load) / max(cap, 1e-9)

        # Distance term: cheap to attach to the end of the open route.
        if not open_route:
            delta = 2.0 * float(inst.dist(0, c))
        else:
            last = open_route[-1]
            delta = float(inst.dist(last, c) + inst.dist(c, 0) - inst.dist(last, 0))

        return (
            self.distance_weight * delta
            + self.load_weight * balance
            - self.slack_weight * slack
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
