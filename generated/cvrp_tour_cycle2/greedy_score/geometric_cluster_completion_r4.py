from math import atan2, hypot, pi, sin, cos

COMPONENT = {
    "name": "geometric_cluster_completion_fast",
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

    Optimized version:
    - Precomputes polar coordinates for all nodes once.
    - Caches route aggregate statistics for open_route tuples.
    - Keeps the exact same scoring logic and outputs.
    """

    __slots__ = (
        "inst",
        "angular_weight",
        "radial_weight",
        "sector_weight",
        "_polar",
        "_route_stats_cache",
    )

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
        depot_x = float(depot[0])
        depot_y = float(depot[1])

        n = self.inst.n_customers
        polar = [None] * (n + 1)
        polar[0] = (0.0, 0.0, 0)
        for node in range(1, n + 1):
            p = self.inst.coords[node]
            x = float(p[0]) - depot_x
            y = float(p[1]) - depot_y
            ang = atan2(y, x)
            rad = hypot(x, y)
            sector = self._sector_id(ang)
            polar[node] = (ang, rad, sector)
        self._polar = tuple(polar)

        self._route_stats_cache = {}

    @staticmethod
    def _angle_diff(a: float, b: float) -> float:
        d = abs(a - b) % (2.0 * pi)
        return min(d, 2.0 * pi - d)

    @staticmethod
    def _sector_id(ang: float, bins: int = 16) -> int:
        x = (ang + pi) / (2.0 * pi)
        idx = int(x * bins)
        if idx >= bins:
            idx = bins - 1
        if idx < 0:
            idx = 0
        return idx

    def _route_stats(self, open_route):
        cached = self._route_stats_cache.get(open_route)
        if cached is not None:
            return cached

        sin_sum = 0.0
        cos_sum = 0.0
        rad_sum = 0.0
        polar = self._polar
        for node in open_route:
            a, r, _ = polar[int(node)]
            sin_sum += sin(a)
            cos_sum += cos(a)
            rad_sum += r

        m = float(len(open_route))
        mean_ang = atan2(sin_sum / m, cos_sum / m)
        mean_rad = rad_sum / m
        route_sector = self._sector_id(mean_ang)
        val = (sin_sum, cos_sum, rad_sum, mean_ang, mean_rad, route_sector)
        self._route_stats_cache[open_route] = val
        return val

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "close":
            return -0.01 * float(len(open_route))

        if kind != "add":
            return 0.0

        c = int(action[1])
        c_ang, c_rad, c_sector = self._polar[c]

        if not open_route:
            sector_count = 0
            angular_mass = 0.0
            radial_mass = 0.0
            polar = self._polar
            for r in remaining:
                r = int(r)
                if r == c:
                    continue
                r_ang, r_rad, r_sector = polar[r]
                if r_sector == c_sector:
                    sector_count += 1
                angular_mass += self._angle_diff(c_ang, r_ang)
                radial_mass += abs(c_rad - r_rad)

            demand_term = float(self.inst.demand[c]) / max(float(self.inst.capacity), 1e-9)

            return (
                self.angular_weight * angular_mass
                + self.radial_weight * radial_mass
                - self.sector_weight * float(sector_count)
                - 0.05 * demand_term
            )

        _, _, _, mean_ang, mean_rad, route_sector = self._route_stats(open_route)

        angular_dist = self._angle_diff(c_ang, mean_ang)
        radial_dist = abs(c_rad - mean_rad)

        sector_mismatch = 0.0 if route_sector == c_sector else 1.0

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
