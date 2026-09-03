from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "bridge_merge_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "window": {"type": "int", "range": [1, 5]},
    },
}


class BridgeMergeSetup:
    """Elimina un setup intermedio cuando el mismo ítem ya está activo en el período anterior
    y posterior, favoreciendo fusiones de bloques consecutivos.
    Movimiento = (i, t, left_bool, right_bool).
    """

    def __init__(self, problem, window=5):
        self.problem = problem
        self.window = int(window)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        for i in range(n_items):
            start_t = 1
            end_t = n_periods - 1
            if self.window < n_periods:
                end_t = min(end_t, self.window - 1 if self.window > 1 else end_t)
            for t in range(start_t, n_periods - 1):
                if sol[i][t - 1] and sol[i][t] and sol[i][t + 1]:
                    yield (i, t, sol[i][t - 1], sol[i][t + 1])

    def apply(self, sol, m):
        i, t, left, right = m
        s = [list(row) for row in sol]
        s[i][t] = False
        s[i][t - 1] = bool(left)
        s[i][t + 1] = bool(right)
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, left, right = m
        s = [list(row) for row in sol]
        s[i][t] = True
        s[i][t - 1] = bool(left)
        s[i][t + 1] = bool(right)
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BridgeMergeSetup(problem, **params)
