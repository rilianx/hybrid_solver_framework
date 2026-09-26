from math import atan2, hypot, pi, sin, cos

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
    """Greedy score for CVRP grand-tour construction.

    Idea:
    - Prefer completing compact geometric clusters around the depot.
    - Use angular-sector density of the remaining customers to seed routes.
    - For an open route, score candidates by how well they fit the whole
      current cluster shape (angular centroid + radial shell), not by
      local end-to-end proximity.
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

        self._polar_cache = {}

    def _coord(self, node: int):
        p = self.inst.coords[node]
        return float(p[0]), float(p[1])

    def _polar(self, node: int):
        node = int(node)
        cached = self._polar_cache.get(node)
        if cached is not None:
            return cached
        x, y = self._coord(node)
        dx = x - self._depot_x
        dy = y - self._depot_y
        val = (atan2(dy, dx), hypot(dx, dy))
        self._polar_cache[node] = val
        return val

    @staticmethod
    def _angle_diff(a: float, b: float) -> float:
        d = abs(a - b) % (2.0 * pi)
        return min(d, 2.0 * pi - d)

    def _sector_id(self, ang: float, bins: int = 16) -> int:
        x = (ang + pi) / (2.0 * pi)
        idx = int(x * bins)
        if idx >= bins:
            idx = bins - 1
        if idx < 0:
            idx = 0
        return idx

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            # Slightly prefer closing already coherent clusters.
            # Shorter routes are cheaper to close in this construction view.
            return -0.01 * float(len(open_route))

        if kind != "add":
            return 0.0

        c = int(action[1])
        c_ang, c_rad = self._polar(c)

        # When starting a route, pick a seed that sits in a dense angular sector
        # of the remaining customers. This is different from nearest-insert logic:
        # it reasons about the global geometric distribution of the still-unbuilt set.
        if not open_route:
            c_sector = self._sector_id(c_ang)

            sector_count = 0
            angular_mass = 0.0
            radial_mass = 0.0
            for r in remaining:
                r = int(r)
                if r == c:
                    continue
                r_ang, r_rad = self._polar(r)
                if self._sector_id(r_ang) == c_sector:
                    sector_count += 1
                angular_mass += self._angle_diff(c_ang, r_ang)
                radial_mass += abs(c_rad - r_rad)

            demand_term = float(self.inst.demand[c]) / max(float(self.inst.capacity), 1e-9)

            # Lower is better:
            # - small angular mass means the customer belongs to a tight angular cluster
            # - more same-sector neighbors makes it a better route seed
            # - moderate radial proximity keeps shells compact
            return (
                self.angular_weight * angular_mass
                + self.radial_weight * radial_mass
                - self.sector_weight * float(sector_count)
                - 0.05 * demand_term
            )

        # For an ongoing route, score the candidate against the whole current
        # partial cluster, not just the last customer.
        sin_sum = 0.0
        cos_sum = 0.0
        rad_sum = 0.0
        for node in open_route:
            a, r = self._polar(int(node))
            sin_sum += sin(a)
            cos_sum += cos(a)
            rad_sum += r

        m = float(len(open_route))
        mean_ang = atan2(sin_sum / m, cos_sum / m)
        mean_rad = rad_sum / m

        angular_dist = self._angle_diff(c_ang, mean_ang)
        radial_dist = abs(c_rad - mean_rad)

        # Extra cluster-density term: favor candidates that stay within the same
        # angular sector as the existing route mass.
        route_sector = self._sector_id(mean_ang)
        candidate_sector = self._sector_id(c_ang)
        sector_mismatch = 0.0 if route_sector == candidate_sector else 1.0

        return (
            self.angular_weight * angular_dist
            + self.radial_weight * radial_dist
            + self.sector_weight * sector_mismatch
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
