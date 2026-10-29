COMPONENT = {
    "name": "insertion_delta_route_penalty",
    "slot": "greedy_score",
    "compatible_skeletons": ['SA', 'ILS', 'TS', 'VNS', 'GRASP', 'LNS_MIP', 'FIX_OPT', 'LOCAL_BRANCH', 'MIP_PERTURB'],
    "requires": [],
    "params": {
        "new_route_penalty": {"type": "float", "range": [0.0, 3.0]},
        "fill_bonus": {"type": "float", "range": [0.0, 1.0]},
    },
}


class InsertionDeltaRoutePenalty:
    """La acción es (c, new_route, delta) y el parcial es (tour, carga, último).
    El puntaje es el delta de distancia de la acción. Abrir una ruta nueva
    teniendo una abierta se penaliza en proporción a la distancia media al
    depósito. Si se continúa la ruta, se premia a los clientes que más llenan
    el vehículo."""

    def __init__(self, problem, new_route_penalty=1.0, fill_bonus=0.3):
        inst = problem.inst
        self.n = inst.n_customers
        self.dem = list(inst.demand)
        self.cap = float(inst.capacity) if inst.capacity > 0 else 1.0
        d0 = [float(inst.dist(0, c)) for c in range(1, self.n + 1)]
        self.avg_d0 = (sum(d0) / len(d0)) if d0 else 1.0
        if self.avg_d0 <= 0:
            self.avg_d0 = 1.0
        self.new_route_penalty = float(new_route_penalty)
        self.fill_bonus = float(fill_bonus)

    def score(self, partial, action):
        c = int(action[0])
        new_route = bool(action[1])
        delta = float(action[2])
        last = partial[2]
        s = delta
        if new_route:
            if last != 0:
                s += self.new_route_penalty * self.avg_d0
        else:
            s -= self.fill_bonus * self.avg_d0 * (self.dem[c] / self.cap)
        return float(s)


def build_component(problem, new_route_penalty: float = 1.0, fill_bonus: float = 0.3):
    return InsertionDeltaRoutePenalty(problem, new_route_penalty, fill_bonus)
