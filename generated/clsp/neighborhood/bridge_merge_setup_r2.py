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
    """Vecindad de eliminación de setups.

    Genera movimientos elementales que apagan un setup activo (i, t).
    La idea sigue siendo favorecer fusiones de bloques consecutivos,
    pero se garantiza que el vecindario no sea vacío cuando existan setups.
    """

    def __init__(self, problem, window=5):
        self.problem = problem
        self.window = int(window)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods

        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue

                # Prioriza setups "puente" entre dos setups vecinos,
                # pero no excluye otros setups activos para evitar vecindarios vacíos.
                if 0 < t < n_periods - 1 and sol[i][t - 1] and sol[i][t + 1]:
                    yield (i, t, True)
                else:
                    yield (i, t, False)

    def apply(self, sol, m):
        i, t, _bridge = m
        s = [list(row) for row in sol]
        s[i][t] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, _bridge = m
        s = [list(row) for row in sol]
        s[i][t] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return BridgeMergeSetup(problem, **params)
