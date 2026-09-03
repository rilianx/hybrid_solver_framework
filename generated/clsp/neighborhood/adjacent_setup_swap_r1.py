from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "adjacent_setup_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "period_span": {"type": "int", "range": [1, 3]},
    },
}


class AdjacentSetupSwap:
    """Intercambia un setup activo de un ítem por un setup inactivo de otro ítem
    en el mismo período. Movimiento = (i_out, i_in, t, old_out, old_in).
    """

    def __init__(self, problem, period_span=1):
        self.problem = problem
        self.period_span = int(period_span)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for t in range(n_periods):
            items_on = [i for i in range(n_items) if sol[i][t]]
            items_off = [i for i in range(n_items) if not sol[i][t]]
            for i_out in items_on:
                for i_in in items_off:
                    yield (i_out, i_in, t, sol[i_out][t], sol[i_in][t])

    def apply(self, sol, m):
        i_out, i_in, t, old_out, old_in = m
        s = [list(row) for row in sol]
        s[i_out][t] = False
        s[i_in][t] = True
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i_out, i_in, t, old_out, old_in = m
        s = [list(row) for row in sol]
        s[i_out][t] = bool(old_out)
        s[i_in][t] = bool(old_in)
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return AdjacentSetupSwap(problem, **params)
