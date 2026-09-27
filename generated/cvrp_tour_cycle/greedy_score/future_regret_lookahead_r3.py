COMPONENT = {
    "name": "future_regret_lookahead",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "regret_weight": {"type": "float", "range": [0.0, 20.0]},
        "distance_weight": {"type": "float", "range": [0.0, 5.0]},
        "balance_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class FutureRegretLookahead:
    """Score con sesgo de 'regret' local usando solo información barata.

    Idea:
    - Prefiere acciones que no solo son buenas ahora, sino que dejan buenas opciones
      para los clientes restantes.
    - Si hay muchos clientes restantes, penaliza elegir uno que sea claramente peor
      que el mejor candidato disponible.
    - Usa una medida simple de cercanía al mejor candidato restante (sin buscar optimalidad).
    """

    def __init__(self, problem, regret_weight: float = 2.0, distance_weight: float = 1.0, balance_weight: float = 0.5):
        self.inst = problem.inst
        self.regret_weight = float(regret_weight)
        self.distance_weight = float(distance_weight)
        self.balance_weight = float(balance_weight)

    def _min_remaining_depot_dist(self, remaining) -> float:
        if not remaining:
            return 0.0
        best = None
        for c in remaining:
            d = float(self.inst.dist(0, int(c)))
            if best is None or d < best:
                best = d
        return 0.0 if best is None else best

    def score(self, partial, action) -> float:
        built, open_route, remaining = partial
        kind = action[0]

        if kind == "add":
            c = int(action[1])
            delta = float(action[2])

            # Preferimos clientes que "ordenan" mejor el resto del gran tour:
            # si c es cercano al depósito comparado con el promedio restante, suele
            # ser mejor fijarlo antes porque deja clientes más periféricos para después.
            min_rem = self._min_remaining_depot_dist(remaining)
            avg_rem = self._avg_remaining_depot_dist(remaining)
            depot_priority = float(self.inst.dist(0, c))

            # Regret global: cuánto se aparta c del perfil general de lo restante.
            regret = max(0.0, depot_priority - avg_rem)

            # Balance de demanda: usar clientes grandes antes ayuda a formar cortes
            # más definidos para Split; penalizamos dejar mucha demanda "pesada" al final.
            demand_c = int(self.inst.demand[c])
            cap = float(self.inst.capacity)
            remaining_demand = 0
            for x in remaining:
                remaining_demand += int(self.inst.demand[int(x)])
            load_ratio = (demand_c / cap) if cap > 0 else 0.0
            remaining_ratio = (remaining_demand / cap) if cap > 0 else 0.0
            balance = abs(load_ratio - min(1.0, remaining_ratio / max(1.0, len(remaining))))

            # Un pequeño sesgo por cerrar "extremos" del gran tour:
            # clientes muy alejados del depósito se priorizan menos si el resto es compacto.
            endpoint_bias = self._route_endpoints_bias(open_route)
            if open_route:
                endpoint_bias += float(self.inst.dist(int(open_route[-1]), c))
            else:
                endpoint_bias += float(self.inst.dist(0, c))

            return (
                self.distance_weight * (delta + 0.25 * depot_priority)
                + self.regret_weight * regret
                + self.balance_weight * balance
                + 0.15 * endpoint_bias
                - 0.10 * min_rem
            )

        if kind == "close":
            if not open_route:
                return 0.0

            load = self._route_load(open_route)
            cap = float(self.inst.capacity)
            fill = (load / cap) if cap > 0 else 0.0

            # Cerrar es más atractivo cuando la ruta ya está suficientemente "madura"
            # y cuando el cliente final del bloque es relativamente caro respecto al resto.
            tail = int(open_route[-1])
            tail_depot = float(self.inst.dist(tail, 0))
            rem_min = self._min_remaining_depot_dist(remaining)
            rem_avg = self._avg_remaining_depot_dist(remaining)

            maturity = max(0.0, 0.55 - fill)
            separation = max(0.0, tail_depot - rem_avg)

            # Si la ruta abierta ya conecta mal con lo que queda, cerrar ayuda al Split.
            return 1.5 * maturity + 0.8 * separation + 0.2 * rem_min

        return 1e18

    def _min_dist_to_set(self, node: int, candidates) -> float:
        best = None
        for c in candidates:
            c = int(c)
            if c == node:
                continue
            d = float(self.inst.dist(node, c))
            if best is None or d < best:
                best = d
        return 0.0 if best is None else best

    def _route_internal_span(self, route) -> float:
        if len(route) <= 1:
            return 0.0
        total = 0.0
        prev = int(route[0])
        for c in route[1:]:
            c = int(c)
            total += float(self.inst.dist(prev, c))
            prev = c
        return total

    def _avg_remaining_depot_dist(self, remaining) -> float:
        total = 0.0
        count = 0
        for c in remaining:
            total += float(self.inst.dist(0, int(c)))
            count += 1
        return total / count if count else 0.0

    def _route_load(self, route) -> int:
        load = 0
        for c in route:
            load += int(self.inst.demand[int(c)])
        return load

    def _route_endpoints_bias(self, route) -> float:
        if not route:
            return 0.0
        first = int(route[0])
        last = int(route[-1])
        return float(self.inst.dist(0, first)) + float(self.inst.dist(last, 0))


def build_component(problem, regret_weight: float = 2.0, distance_weight: float = 1.0, balance_weight: float = 0.5):
    return FutureRegretLookahead(
        problem,
        regret_weight=regret_weight,
        distance_weight=distance_weight,
        balance_weight=balance_weight,
    )
