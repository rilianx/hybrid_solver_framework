import math

COMPONENT = {
    "name": "polar_sweep_angle_gap",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {"dist_weight": {"type": "float", "range": [0.0, 1.0]}},
}

_CLOSE_SCORE = 1e12
_TWO_PI = 2.0 * math.pi


class PolarSweepAngleGap:
    """Heurística de barrido: cada cliente tiene un ángulo polar respecto al depósito
    (coordenadas reconstruidas desde las distancias). El puntaje es el avance angular
    antihorario desde el ángulo de referencia actual (último cliente de la ruta abierta,
    o último de la ruta anterior), más un término de distancia que desempata. Las rutas
    resultan sectores angulares contiguos; solo se cierra cuando nada más cabe."""

    def __init__(self, problem, dist_weight: float = 0.2):
        self.inst = problem.inst
        self.dist_weight = float(dist_weight)
        self.angle = {}
        self._build_angles()

    def _build_angles(self):
        inst = self.inst
        dist = inst.dist
        custs = sorted(int(c) for c in inst.customers)
        if not custs:
            self.scale = 1.0
            return
        d0 = {c: float(dist(0, c)) for c in custs}
        tot = sum(d0.values())
        self.scale = tot / len(custs) if tot > 0 else 1.0
        a = max(custs, key=lambda c: (d0[c], -c))
        xa = d0[a]
        if xa <= 1e-12:
            for c in custs:
                self.angle[c] = 0.0
            return
        xy = {}
        for c in custs:
            dac = float(dist(a, c)) if c != a else 0.0
            x = (d0[c] ** 2 + xa ** 2 - dac ** 2) / (2.0 * xa)
            y = math.sqrt(max(0.0, d0[c] ** 2 - x * x))
            xy[c] = (x, y)
        b = max(custs, key=lambda c: (xy[c][1], -c))
        xb, yb = xy[b]
        for c in custs:
            x, y = xy[c]
            if yb > 1e-9 and y > 1e-12 and c != b:
                dbc = float(dist(b, c))
                e_pos = abs(math.hypot(x - xb, y - yb) - dbc)
                e_neg = abs(math.hypot(x - xb, -y - yb) - dbc)
                if e_neg < e_pos:
                    y = -y
            ang = math.atan2(y, x) % _TWO_PI
            self.angle[c] = ang if math.isfinite(ang) else 0.0

    def _ref(self, partial):
        built, open_route = partial[0], partial[1]
        if open_route:
            last = open_route[-1]
            return self.angle.get(last, 0.0), last
        if built:
            for r in reversed(built):
                if r:
                    return self.angle.get(r[-1], 0.0), 0
        return 0.0, 0

    def score(self, partial, action):
        if action[0] != "add":
            return _CLOSE_SCORE
        c = int(action[1])
        theta_ref, last = self._ref(partial)
        gap = (self.angle.get(c, 0.0) - theta_ref) % _TWO_PI
        val = gap / _TWO_PI + self.dist_weight * self.inst.dist(last, c) / self.scale
        if not math.isfinite(val):
            return _CLOSE_SCORE / 2.0
        return float(val)


def build_component(problem, dist_weight: float = 0.2):
    return PolarSweepAngleGap(problem, dist_weight)
