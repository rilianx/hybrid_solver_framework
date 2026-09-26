COMPONENT = {
    "name": "geometric_cluster_completion",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "centroid_weight": {"type": "float", "range": [0.0, 5.0]},
        "compactness_weight": {"type": "float", "range": [0.0, 5.0]},
        "route_end_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class GeometricClusterCompletion:
    """CVRP grand-tour construction heuristic.

    Idea:
    - Build routes that are geometrically compact.
    - Prefer customers close to the current route end and close to the depot.
    - Add a centroid-like term using the route's current average position to promote
      spatial clustering rather than only local insertion cost.

    This differs from the previous heuristics because it focuses on geometric cohesion
    of the route, not on capacity fill or pure insertion cost.
    """

    def __init__(
        self,
        problem,
        centroid_weight: float = 1.0,
        compactness_weight: float = 1.0,
        route_end_weight: float = 1.0,
    ):
        self.inst = problem.inst
        self.centroid_weight = float(centroid_weight)
        self.compactness_weight = float(compactness_weight)
        self.route_end_weight = float(route_end_weight)

    def _coord(self, node: int):
        inst = self.inst
        p = inst.coords[node]
        return float(p[0]), float(p[1])

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]
        inst = self.inst

        if kind == "close":
            # Close when the current route is already geometrically coherent:
            # shorter open route => slightly more attractive to close.
            route_len = len(open_route)
            return -0.1 * float(route_len)

        if kind != "add":
            return 0.0

        c = int(action[1])
        cx, cy = self._coord(c)

        # Depot proximity: helps start routes near the depot-friendly customers.
        depot_x, depot_y = self._coord(0)
        depot_dist = ((cx - depot_x) ** 2 + (cy - depot_y) ** 2) ** 0.5

        if not open_route:
            # Starting a new route: use depot proximity plus a mild demand tie-breaker.
            demand_term = float(inst.demand[c]) / max(float(inst.capacity), 1e-9)
            return depot_dist - 0.05 * demand_term

        last = open_route[-1]
        lx, ly = self._coord(last)
        end_dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5

        # Current route centroid (computed cheaply from the already built open route).
        sx = sy = 0.0
        for node in open_route:
            x, y = self._coord(node)
            sx += x
            sy += y
        m = float(len(open_route))
        mx = sx / m
        my = sy / m
        centroid_dist = ((cx - mx) ** 2 + (cy - my) ** 2) ** 0.5

        # Prefer customers that are both close to the route end and close to the current cluster.
        return (
            self.route_end_weight * end_dist
            + self.centroid_weight * centroid_dist
            + self.compactness_weight * depot_dist
        )


def build_component(
    problem,
    centroid_weight: float = 1.0,
    compactness_weight: float = 1.0,
    route_end_weight: float = 1.0,
):
    return GeometricClusterCompletion(
        problem,
        centroid_weight=centroid_weight,
        compactness_weight=compactness_weight,
        route_end_weight=route_end_weight,
    )
