from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "redundant_setup_pruner",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "lookback_limit": {"type": "int", "range": [1, 999]},
    },
}


class RedundantSetupPruner:
    """Elimina un setup redundante de un ítem cuando ya existía un setup previo.
    Movimiento = (i, t, prev_t_bool).
    """

    def __init__(self, problem, lookback_limit=999):
        self.problem = problem
        self.lookback_limit = int(lookback_limit)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for i in range(n_items):
            start_t = max(1, n_periods - self.lookback_limit) if self.lookback_limit < n_periods else 1
            for t in range(start_t, n_periods):
                if sol[i][t] and sol[i][t - 1]:
                    yield (i, t, sol[i][t - 1])

    def apply(self, sol, m):
        i, t, prev = m
        s = [list(row) for row in sol]
        s[i][t] = False
        s[i][t - 1] = bool(prev)
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, prev = m
        s = [list(row) for row in sol]
        s[i][t] = True
        s[i][t - 1] = bool(prev)
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return RedundantSetupPruner(problem, **params)
