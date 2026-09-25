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
    """Vecindario de intercambio por congestión temporal.

    Movimiento elemental:
        (i, j, t_from, t_to) con i < j y t_from != t_to

    Patrón esperado al generar el movimiento:
        sol[i][t_from] = True,  sol[i][t_to] = False
        sol[j][t_from] = False, sol[j][t_to] = True

    La aplicación realiza una transformación involutiva sobre esas cuatro
    posiciones, de modo que undo(apply(sol, m)) == sol.
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

        for i in range(n_items):
            for j in range(i + 1, n_items):
                for t_from in period_order:
                    if not sol[i][t_from] or sol[j][t_from]:
                        continue
                    for t_to in reversed(period_order):
                        if t_to == t_from:
                            continue
                        if sol[i][t_to] or not sol[j][t_to]:
                            continue
                        yield (i, j, t_from, t_to)

    def apply(self, sol, m):
        i, j, t_from, t_to = m
        s = [list(row) for row in sol]

        # Transformación involutiva sobre las cuatro posiciones implicadas.
        # Para el patrón válido 1,0,0,1 produce 0,1,1,0; aplicada dos veces
        # retorna al estado original.
        s[i][t_from] = not s[i][t_from]
        s[i][t_to] = not s[i][t_to]
        s[j][t_from] = not s[j][t_from]
        s[j][t_to] = not s[j][t_to]

        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return PeriodCapacitySwap(problem)
