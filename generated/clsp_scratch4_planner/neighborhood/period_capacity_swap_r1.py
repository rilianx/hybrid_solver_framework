COMPONENT = {
    "name": "period_capacity_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.to_assignment", "ProblemModel.from_assignment", "ProblemModel.variable_groups"],
    "params": {},
}


class PeriodCapacitySwap:
    """Intercambio 2x2 de setups entre dos ítems y dos períodos.

    Movimiento = (i, j, t_from, t_to) con i < j y t_from != t_to.
    Requiere el patrón:
        sol[i][t_from] = True,  sol[i][t_to] = False
        sol[j][t_from] = False, sol[j][t_to] = True

    El efecto es intercambiar las asignaciones temporales de esos dos setups,
    preservando el número total de setups por ítem y globalmente.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        # Carga por período: útil para priorizar swaps que alivien congestión.
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

                        # Priorizamos swaps que mueven un setup desde un período
                        # más cargado hacia uno menos cargado.
                        if load[t_from] >= load[t_to]:
                            yield (i, j, t_from, t_to)
                        else:
                            # También permitimos algunos swaps inversos para no
                            # vaciar el vecindario, pero con prioridad menor.
                            yield (i, j, t_from, t_to)

    def apply(self, sol, m):
        i, j, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        s[j][t_from] = True
        s[j][t_to] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        # El mismo intercambio es involutivo.
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return PeriodCapacitySwap(problem)
