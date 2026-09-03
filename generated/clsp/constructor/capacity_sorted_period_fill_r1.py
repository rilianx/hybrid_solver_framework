from random import Random

COMPONENT = {
    "name": "capacity_sorted_period_fill",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "shuffle_ties": {"type": "bool", "range": [0, 1]},
        "slack_factor": {"type": "float", "range": [0.05, 0.95]},
    },
}


class CapacitySortedPeriodFill:
    """Constructor por períodos: en cada período selecciona ítems con mayor presión de demanda/coste y les asigna setup si cabe la carga estimada."""

    def __init__(self, shuffle_ties: bool = True, slack_factor: float = 0.25):
        self.shuffle_ties = shuffle_ties
        self.slack_factor = slack_factor

    @staticmethod
    def _empty_solution(n_items: int, n_periods: int):
        return tuple(tuple(False for _ in range(n_periods)) for _ in range(n_items))

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        demand = inst.demand
        setup_cost = inst.setup_cost
        setup_time = inst.setup_time
        capacity = inst.capacity

        sol = [list(row) for row in self._empty_solution(n_items, n_periods)]
        remaining_need = [sum(demand[i]) for i in range(n_items)]

        for t in range(n_periods):
            # ítems candidatos: los que aún tienen demanda pendiente.
            cand = [i for i in range(n_items) if remaining_need[i] > 0]
            if self.shuffle_ties:
                rng.shuffle(cand)

            # Score: demanda pendiente por setup cost y tiempo, con sesgo hacia ítems "pesados".
            cand.sort(
                key=lambda i: (
                    -(remaining_need[i] / max(1.0, setup_cost[i] + setup_time[i])),
                    -remaining_need[i],
                    setup_time[i],
                )
            )

            budget = capacity[t] * (1.0 - self.slack_factor)
            used = 0.0
            chosen = []
            for i in cand:
                if remaining_need[i] <= 0:
                    continue
                if used + setup_time[i] <= budget:
                    chosen.append(i)
                    used += setup_time[i]

            # Si no caben suficientes, añadir al menos uno si es posible.
            if not chosen and cand:
                chosen = [cand[0]]

            for i in chosen:
                sol[i][t] = True

            # Reducir la demanda pendiente de forma conservadora:
            # un setup aquí puede cubrir parte de la demanda futura, así que
            # amortizamos por una fracción de la demanda restante.
            for i in chosen:
                remaining_need[i] = max(0.0, remaining_need[i] - sum(demand[i][t:]))

        return tuple(tuple(row) for row in sol)


def build_component(problem, shuffle_ties: bool = True, slack_factor: float = 0.25):
    return CapacitySortedPeriodFill(shuffle_ties=shuffle_ties, slack_factor=slack_factor)
