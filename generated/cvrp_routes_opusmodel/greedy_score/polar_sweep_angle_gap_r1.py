import math

COMPONENT = {
    "name": "polar_sweep_angle_gap",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "start_angle": {"type": "float", "range": [-3.1416, 3.1416]},
        "dist_weight": {"type": "float", "range": [0.0, 2.0]},
        "close_margin": {"type": "float", "range": [0.01, 1.0]},
    },
}


class PolarSweepAngleGap:
    """add: hueco angular ccw (desde el último cliente de la ruta actual o de la última ruta cerrada,
    o desde start_angle) normalizado a la escala de distancias, más dist_weight·d(last,c).
    close: mejor 'add' factible + margen (rutas llenas tipo sweep)."""

    def __init__(self, problem, start_angle=0.0, dist_weight=0.5, close_margin=0.1):
        inst = problem.inst
        self.inst = inst
        self.start = float(start_angle)
        self.w = float(dist_weight)
        self.margin = float(close_margin)
        self.cap = float(inst.capacity) + 1e-9
        x0, y0 = inst.coords[0]
        self.ang = {}
        for c in inst.customers:
            x, y = inst.coords[c]
            self.ang[c] = math.atan2(y - y0, x - x0)
        custs = list(inst.customers)
        self.scale = (sum(inst.dist(0, c) for c in custs) / len(custs)) if custs else 1.0
        if not (self.scale > 0) or not math.isfinite(self.scale):
            self.scale = 1.0

    def _ref(self, closed, cur):
        if cur:
            return self.ang[cur[-1]]
        if closed and closed[-1]:
            return self.ang[closed[-1][-1]]
        return self.start

    def _add_score(self, ref, last, c):
        gap = (self.ang[c] - ref) % (2.0 * math.pi)
        return self.scale * gap + self.w * self.inst.dist(last, c)

    def score(self, partial, action):
        closed, cur, load, remaining = partial
        last = cur[-1] if cur else 0
        ref = self._ref(closed, cur)
        if action[0] == "close":
            best = None
            for c in remaining:
                if load + self.inst.demand[c] <= self.cap:
                    s = self._add_score(ref, last, c)
                    if best is None or s < best:
                        best = s
            if best is None:
                return 0.0
            return float(best + self.margin * (abs(best) + self.scale))
        return float(self._add_score(ref, last, int(action[1])))


def build_component(problem, start_angle=0.0, dist_weight=0.5, close_margin=0.1):
    return PolarSweepAngleGap(problem, start_angle, dist_weight, close_margin)
