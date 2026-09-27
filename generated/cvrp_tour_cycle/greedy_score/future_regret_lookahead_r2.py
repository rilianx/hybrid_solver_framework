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

            # Mirada a la continuidad del gran tour:
            # - qué tan bien encaja c con el extremo actual
            # - qué tan buenas quedan las opciones futuras alrededor de c
            if open_route:
                tail = int(open_route[-1])
                attach_cost = float(self.inst.dist(tail, c))
                tail_future = self._min_dist_to_set(tail, remaining)
            else:
                attach_cost = 0.0
                # Si arrancamos una nueva ruta, preferimos un inicio que
                # no "rompa" las posibilidades futuras.
                tail_future = 0.0

            c_future = self._min_dist_to_set(c, remaining)

            # Regret local: penaliza clientes "aislados" respecto del resto no construido.
            regret = max(0.0, c_future - tail_future)

            # Balance de carga: evita que la ruta abierta se quede demasiado vacía o demasiado cargada.
            load = sum(int(self.inst.demand[x]) for x in open_route) if open_route else 0
            demand_c = int(self.inst.demand[c])
            cap = float(self.inst.capacity)
            fill_after = (load + demand_c) / cap if cap > 0 else 0.0
            balance = abs(0.5 - min(1.0, max(0.0, fill_after)))

            # El delta del constructor sigue importando, pero ahora la prioridad
            # principal es la compatibilidad con el "frente" del tour.
            return (
                self.distance_weight * (delta + attach_cost)
                + self.regret_weight * regret
                + self.balance_weight * balance
            )

        if kind == "close":
            if not open_route:
                return 0.0

            tail = int(open_route[-1])
            rem_near_tail = self._min_dist_to_set(tail, remaining)

            load = sum(int(self.inst.demand[c]) for c in open_route)
            cap = float(self.inst.capacity)
            fill = load / cap if cap > 0 else 0.0

            # Si la ruta ya es internamente coherente y el extremo actual está
            # poco conectado con lo que queda, cerrar es más atractivo.
            internal_span = self._route_internal_span(open_route)
            coherence = internal_span / max(1, len(open_route) - 1)

            underfill_penalty = max(0.0, 0.65 - fill)

            return rem_near_tail + 0.25 * coherence + 2.0 * underfill_penalty

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


def build_component(problem, regret_weight: float = 2.0, distance_weight: float = 1.0, balance_weight: float = 0.5):
    return FutureRegretLookahead(
        problem,
        regret_weight=regret_weight,
        distance_weight=distance_weight,
        balance_weight=balance_weight,
    )
