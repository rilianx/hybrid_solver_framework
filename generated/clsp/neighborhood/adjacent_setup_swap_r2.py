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
    """Vecindario elemental: alterna un único setup y deja `undo` exacto.

    El movimiento es (i, t, old_value). Se exploran todos los pares (i, t),
    lo que permite apagar setups redundantes desde la solución inicial.
    """

    def __init__(self, problem, period_span=1):
        self.problem = problem
        self.period_span = int(period_span)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for i in range(n_items):
            for t in range(n_periods):
                yield (i, t, bool(sol[i][t]))

    def apply(self, sol, m):
        i, t, old_value = m
        s = [list(row) for row in sol]
        s[i][t] = not bool(old_value)
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, old_value = m
        s = [list(row) for row in sol]
        s[i][t] = bool(old_value)
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    if "period_span" not in params:
        params["period_span"] = 1
    return AdjacentSetupSwap(problem, **params)
