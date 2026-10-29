import math

COMPONENT = {
    "name": "polar_sweep_angle",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "angle_weight": {"type": "float", "range": [0.1, 5.0]},
        "route_bias": {"type": "float", "range": [0.0, 3.0]},
    },
}


class PolarSweepAngle:
    """Recorre los clientes por ángulo polar alrededor del depósito, en sentido
    antihorario a partir del ángulo del último nodo. El puntaje combina el
    avance angular normalizado con la distancia normalizada desde el último
    nodo. Abrir ruta nueva teniendo una abierta suma un sesgo, de modo que las
    rutas salen como sectores contiguos."""

    def __init__(self, problem, angle_weight=1.0, route_bias=1.0):
        inst = problem.inst
        self.inst = inst
        n = inst.n_customers
        x0, y0 = inst.coords[0]
        self.theta = [0.0] * (n + 1)
        for c in range(1, n + 1):
            x, y = inst.coords[c]
            self.theta[c] = math.atan2(y - y0, x - x0)
        self.start = (min(self.theta[1:]) - 1e-9) if n > 0 else 0.0
        d0 = [float(inst.dist(0, c)) for c in range(1, n + 1)]
        self.scale = max(max(d0) if d0 else 1.0, 1e-9)
        self.angle_weight = float(angle_weight)
        self.route_bias = float(route_bias)
        self.two_pi = 2.0 * math.pi

    def score(self, partial, action):
        c = int(action[0])
        new_route = bool(action[1])
        last = partial[2]
        if last == 0:
            ref = self.start
            d = float(self.inst.dist(0, c))
        else:
            ref = self.theta[last]
            d = float(self.inst.dist(last, c)) if not new_route else float(self.inst.dist(0, c))
        gap = (self.theta[c] - ref) % self.two_pi
        s = self.angle_weight * gap / self.two_pi + d / self.scale
        if new_route and last != 0:
            s += self.route_bias
        if not math.isfinite(s):
            s = 1e12
        return float(s)


def build_component(problem, angle_weight: float = 1.0, route_bias: float = 1.0):
    return PolarSweepAngle(problem, angle_weight, route_bias)
