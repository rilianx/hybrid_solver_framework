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
    """Constructor por períodos con llenado capacitado y reparación por factibilidad."""

    def __init__(self, shuffle_ties: bool = True, slack_factor: float = 0.25):
        self.shuffle_ties = shuffle_ties
        self.slack_factor = slack_factor

    @staticmethod
    def _new_matrix(n_items: int, n_periods: int, value: bool = False):
        return [[value for _ in range(n_periods)] for _ in range(n_items)]

    @staticmethod
    def _copy_solution(sol):
        return tuple(tuple(row) for row in sol)

    def _period_usage(self, sol, inst, t: int) -> float:
        return sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])

    def _item_score(self, inst, i: int, t: int, remaining, demand_suffix):
        # Mayor demanda restante, más urgente al acercarse el final y setups más baratos.
        setup_time = inst.setup_time[i]
        setup_cost = inst.setup_cost[i]
        urgency = demand_suffix[i][t]
        return (
            remaining[i] + 0.5 * urgency,
            remaining[i],
            -float(setup_time),
            -float(setup_cost),
        )

    def _build_initial(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = self._new_matrix(n_items, n_periods, False)

        demand_suffix = [
            [0 for _ in range(n_periods)]
            for _ in range(n_items)
        ]
        for i in range(n_items):
            acc = 0
            for t in range(n_periods - 1, -1, -1):
                acc += inst.demand[i][t]
                demand_suffix[i][t] = acc

        remaining = [sum(inst.demand[i]) for i in range(n_items)]

        for t in range(n_periods):
            cap = float(inst.capacity[t])
            budget = cap * (1.0 - self.slack_factor)
            if budget < 0:
                budget = 0.0

            cand = [i for i in range(n_items) if remaining[i] > 0]
            if self.shuffle_ties:
                rng.shuffle(cand)
            cand.sort(key=lambda i: self._item_score(inst, i, t, remaining, demand_suffix), reverse=True)

            used = 0.0
            chosen = []

            # Primer pase: llenar respetando un presupuesto conservador.
            for i in cand:
                st = inst.setup_time[i]
                if used + st <= budget:
                    sol[i][t] = True
                    chosen.append(i)
                    used += st

            # Segundo pase: si quedó hueco, intentar mejorar la cobertura con el resto.
            if used < cap:
                for i in cand:
                    if sol[i][t]:
                        continue
                    st = inst.setup_time[i]
                    if used + st <= cap:
                        sol[i][t] = True
                        chosen.append(i)
                        used += st

            # Si el período quedó vacío y hay demanda pendiente, activar el ítem más prioritario
            # siempre que quepa su setup.
            if not chosen and cand:
                i = cand[0]
                if inst.setup_time[i] <= cap:
                    sol[i][t] = True
                    chosen.append(i)

            # Disminuir la presión de demanda de los ítems activados.
            for i in chosen:
                # Una activación en t ayuda a cubrir la demanda pendiente futura.
                remaining[i] = max(0, remaining[i] - int(demand_suffix[i][t]))

        return self._copy_solution(sol)

    def _repair(self, sol, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        max_iter = n_items * n_periods * 4

        for _ in range(max_iter):
            if inst.problem.is_feasible(sol) if hasattr(inst, "problem") else False:
                return sol

            # Reparación conservadora: agregar setups en períodos con capacidad disponible,
            # priorizando ítems con mayor demanda total.
            changed = False
            item_rank = sorted(range(n_items), key=lambda i: sum(inst.demand[i]), reverse=True)

            for t in range(n_periods):
                used = self._period_usage(sol, inst, t)
                spare = float(inst.capacity[t]) - used
                if spare <= 0:
                    continue
                for i in item_rank:
                    if sol[i][t]:
                        continue
                    st = inst.setup_time[i]
                    if st <= spare:
                        row = list(sol[i])
                        row[t] = True
                        sol = tuple(sol[:i] + (tuple(row),) + sol[i + 1 :])
                        spare -= st
                        changed = True
                    if spare <= 0:
                        break

            if not changed:
                break

        return sol

    def build(self, inst, rng: Random):
        sol = self._build_initial(inst, rng)

        # Intento de reparación con apoyo de la comprobación de factibilidad si está disponible.
        if hasattr(inst, "problem") and hasattr(inst.problem, "is_feasible"):
            if not inst.problem.is_feasible(sol):
                sol = self._repair(sol, inst, rng)

        return sol


def build_component(problem, shuffle_ties: bool = True, slack_factor: float = 0.25):
    return CapacitySortedPeriodFill(shuffle_ties=shuffle_ties, slack_factor=slack_factor)
