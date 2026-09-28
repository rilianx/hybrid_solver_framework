from math import atan2, hypot, pi

COMPONENT = {
    "name": "geometric_cluster_completion",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "angular_weight": {"type": "float", "range": [0.0, 5.0]},
        "radial_weight": {"type": "float", "range": [0.0, 5.0]},
        "sector_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class GeometricClusterCompletion:
    """CVRP grand-tour construction heuristic based on angular clustering.

    Idea:
    - Build the tour by staying within the same geometric sector around the depot.
    - Prefer customers with similar polar angle to the current partial tour.
    - Use radial similarity as a secondary cue, instead of local route-end proximity.
    """

    def __init__(
        self,
        problem,
        angular_weight: float = 1.0,
        radial_weight: float = 1.0,
        sector_weight: float = 1.0,
    ):
        self.inst = problem.inst
        self.angular_weight = float(angular_weight)
        self.radial_weight = float(radial_weight)
        self.sector_weight = float(sector_weight)
        depot = self.inst.coords[0]
        self._depot_x = float(depot[0])
        self._depot_y = float(depot[1])

    def _coord(self, node: int):
        p = self.inst.coords[node]
        return float(p[0]), float(p[1])

    def _polar(self, node: int):
        x, y = self._coord(node)
        dx = x - self._depot_x
        dy = y - self._depot_y
        return atan2(dy, dx), hypot(dx, dy)

    @staticmethod
    def _angle_diff(a: float, b: float) -> float:
        d = abs(a - b) % (2.0 * pi)
        return min(d, 2.0 * pi - d)

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            # Encourage closing when the current sector is already coherent.
            # Shorter open routes are slightly more attractive to close.
            return -0.01 * float(len(open_route))

        if kind != "add":
            return 0.0

        c = int(action[1])
        c_ang, c_rad = self._polar(c)

        # Starting a new route: prefer customers in dense angular regions rather than
        # simply the nearest-to-depot ones.
        if not open_route:
            sector_penalty = 0.0
            for r in remaining:
                if r == c:
                    continue
                r_ang, _ = self._polar(int(r))
                sector_penalty += self._angle_diff(c_ang, r_ang)
            demand_term = float(self.inst.demand[c]) / max(float(self.inst.capacity), 1e-9)
            return (
                self.angular_weight * sector_penalty
                + self.radial_weight * c_rad
                - 0.05 * demand_term
            )

        # For an ongoing partial route, preserve angular consistency with the current
        # set of already chosen customers. This uses the whole current structure rather
        # than only the route end.
        ang_sum = 0.0
        sin_sum = 0.0
        cos_sum = 0.0
        rad_sum = 0.0
        m = float(len(open_route))
        for node in open_route:
            a, r = self._polar(int(node))
            ang_sum += a
            sin_sum += float(__import__("math").sin(a))
            cos_sum += float(__import__("math").cos(a))
            rad_sum += r

        # Circular mean of angles in the current route.
        mean_ang = atan2(sin_sum / m, cos_sum / m)
        mean_rad = rad_sum / m

        angular_dist = self._angle_diff(c_ang, mean_ang)
        radial_dist = abs(c_rad - mean_rad)

        # Mild preference for continuing with customers that keep the sector compact.
        # This is distinct from nearest insertion because it scores a geometric region
        # around the route, not the last node.
        return (
            self.angular_weight * angular_dist
            + self.radial_weight * radial_dist
            + self.sector_weight * (angular_dist * 0.5 + radial_dist * 0.5)
        )


def build_component(
    problem,
    angular_weight: float = 1.0,
    radial_weight: float = 1.0,
    sector_weight: float = 1.0,
):
    return GeometricClusterCompletion(
        problem,
        angular_weight=angular_weight,
        radial_weight=radial_weight,
        sector_weight=sector_weight,
    )
