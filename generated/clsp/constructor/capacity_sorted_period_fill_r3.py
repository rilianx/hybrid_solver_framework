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
    """Constructor por períodos con llenado capacitado y factibilidad conservadora."""

    def __init__(self, shuffle_ties: bool = True, slack_factor: float = 0.25):
        self.shuffle_ties = shuffle_ties
        self.slack_factor = slack_factor

    @staticmethod
    def _new_matrix(n_items: int, n_periods: int, value: bool = False):
        return [[value for _ in range(n_periods)] for _ in range(n_items)]

    @staticmethod
    def _as_solution(matrix):
        return tuple(tuple(row) for row in matrix)

    @staticmethod
    def _period_setup_usage(sol, inst, t: int) -> float:
        return sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])

    def _item_priority(self, inst, i: int, t: int, remaining_total, demand_suffix):
        # Mayor demanda pendiente, mayor urgencia al acercarse el final, y setups más baratos primero.
        return (
            remaining_total[i] + 0.25 * demand_suffix[i][t],
            demand_suffix[i][t],
            -float(inst.setup_time[i]),
            -float(inst.setup_cost[i]),
            -i,
        )

    def _build_initial(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = self._new_matrix(n_items, n_periods, False)

        demand_suffix = [[0 for _ in range(n_periods)] for _ in range(n_items)]
        remaining_total = [0 for _ in range(n_items)]
        for i in range(n_items):
            acc = 0
            for t in range(n_periods - 1, -1, -1):
                acc += inst.demand[i][t]
                demand_suffix[i][t] = acc
            remaining_total[i] = acc

        # Cobertura progresiva: cada período activa ítems con demanda pendiente,
        # manteniendo un colchón conservador de capacidad por período.
        for t in range(n_periods):
            cap = float(inst.capacity[t])
            if cap <= 0:
                continue

            # Reserva conservadora para no saturar el período con setups.
            budget = cap * (1.0 - self.slack_factor)
            if budget < 0.0:
                budget = 0.0
            if budget > cap:
                budget = cap

            candidates = [i for i in range(n_items) if remaining_total[i] > 0]
            if self.shuffle_ties:
                rng.shuffle(candidates)
            candidates.sort(
                key=lambda i: self._item_priority(inst, i, t, remaining_total, demand_suffix),
                reverse=True,
            )

            used = self._period_setup_usage(sol, inst, t)

            # Primer pase: usar el presupuesto conservador.
            for i in candidates:
                if remaining_total[i] <= 0 or sol[i][t]:
                    continue
                st = inst.setup_time[i]
                if used + st <= budget:
                    sol[i][t] = True
                    used += st

            # Segundo pase: completar con cualquier hueco remanente del período.
            for i in candidates:
                if remaining_total[i] <= 0 or sol[i][t]:
                    continue
                st = inst.setup_time[i]
                if used + st <= cap:
                    sol[i][t] = True
                    used += st

            # Si no se pudo activar nada y todavía hay demanda pendiente,
            # intentar al menos un setup factible en este período.
            if not any(sol[i][t] for i in range(n_items)):
                for i in candidates:
                    st = inst.setup_time[i]
                    if st <= cap:
                        sol[i][t] = True
                        break

            # Reducir prioridad de los ítems que ya tienen soporte temprano.
            for i in range(n_items):
                if sol[i][t]:
                    remaining_total[i] = max(0, remaining_total[i] - demand_suffix[i][t])

        return self._as_solution(sol)

    def _repair_by_adding(self, sol, inst, rng: Random, max_rounds: int = 6):
        """Reparación conservadora: añade setups solo cuando existe capacidad residual."""
        n_items, n_periods = inst.n_items, inst.n_periods
        for _ in range(max_rounds):
            if inst.problem.is_feasible(sol):
                return sol

            changed = False
            item_rank = sorted(range(n_items), key=lambda i: sum(inst.demand[i]), reverse=True)

            for t in range(n_periods):
                used = self._period_setup_usage(sol, inst, t)
                spare = float(inst.capacity[t]) - used
                if spare <= 0:
                    continue

                candidates = item_rank[:]
                if self.shuffle_ties:
                    rng.shuffle(candidates)

                for i in candidates:
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

        # Si el modelo expone comprobación de factibilidad, usarla para reparar.
        if hasattr(inst, "problem") and hasattr(inst.problem, "is_feasible"):
            if not inst.problem.is_feasible(sol):
                sol = self._repair_by_adding(sol, inst, rng)

        return sol


def build_component(problem, shuffle_ties: bool = True, slack_factor: float = 0.25):
    return CapacitySortedPeriodFill(shuffle_ties=shuffle_ties, slack_factor=slack_factor)
