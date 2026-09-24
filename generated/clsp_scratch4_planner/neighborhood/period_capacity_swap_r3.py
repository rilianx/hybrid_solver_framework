COMPONENT = {
    "name": "period_capacity_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": [
        "ProblemModel.objective",
        "ProblemModel.to_assignment",
        "ProblemModel.from_assignment",
        "ProblemModel.variable_groups",
    ],
    "params": {},
}


class PeriodCapacitySwap:
    """Vecindario de reubicación/intercambio temporal por congestión.

    Movimiento elemental:
        (i, j, t_from, t_to)

    Interpretación:
        - retirar un setup activo de (i, t_from)
        - activar un setup en (j, t_to)

    Es un movimiento involutivo: aplicar el mismo movimiento dos veces
    devuelve la solución original.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        load = []
        for t in range(n_periods):
            used = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    used += self.inst.setup_time[i]
            load.append(used)

        period_order = sorted(range(n_periods), key=lambda t: load[t], reverse=True)

        for t_from in period_order:
            for t_to in reversed(period_order):
                if t_to == t_from:
                    continue
                # Preferir aliviar períodos cargados hacia menos cargados.
                for i in range(n_items):
                    if not sol[i][t_from]:
                        continue
                    for j in range(n_items):
                        if sol[j][t_to]:
                            continue
                        if i == j and t_from == t_to:
                            continue
                        yield (i, j, t_from, t_to)

    def apply(self, sol, m):
        i, j, t_from, t_to = m
        s = [list(row) for row in sol]

        # Movimiento elemental involutivo: desconecta un setup y conecta otro.
        s[i][t_from] = not s[i][t_from]
        s[j][t_to] = not s[j][t_to]

        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return PeriodCapacitySwap(problem)
