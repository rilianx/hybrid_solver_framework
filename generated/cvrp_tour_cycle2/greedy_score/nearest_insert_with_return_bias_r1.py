COMPONENT = {
    "name": "nearest_insert_with_return_bias",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "return_weight": {"type": "float", "range": [0.0, 5.0]},
        "urgency_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class NearestInsertWithReturnBias:
    """CVRP grand-tour construction heuristic.

    Idea:
    - For an "add" action, prefer the customer that minimally increases the current open route,
      i.e., the cheapest insertion at the end of the route.
    - Add a small urgency term that rewards serving customers with large demand earlier.
    - For "close", prefer closing only when the current route is already relatively long;
      otherwise keep extending it.
    """

    def __init__(self, problem, return_weight: float = 1.0, urgency_weight: float = 0.5):
        self.inst = problem.inst
        self.return_weight = float(return_weight)
        self.urgency_weight = float(urgency_weight)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            # Closing is better when the route already has many customers, so that
            # the framework tends to avoid too many tiny routes.
            route_len = len(open_route)
            remaining_count = len(remaining)
            return -self.return_weight * float(route_len) + 0.01 * float(remaining_count)

        if kind != "add":
            return 0.0

        c = int(action[1])
        inst = self.inst
        d = float(inst.demand[c])

        if not open_route:
            delta = 2.0 * float(inst.dist(0, c))
        else:
            last = open_route[-1]
            delta = float(inst.dist(last, c) + inst.dist(c, 0) - inst.dist(last, 0))

        # Smaller delta is better. Larger demand gets a slight priority to avoid
        # leaving high-demand customers for later.
        urgency = d / max(float(inst.capacity), 1e-9)

        # Mild tie-breaker: shorter customers are cheaper to insert in the tour
        # if distance effects are similar.
        return delta - self.urgency_weight * urgency


def build_component(problem, return_weight: float = 1.0, urgency_weight: float = 0.5):
    return NearestInsertWithReturnBias(problem, return_weight=return_weight, urgency_weight=urgency_weight)
