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
    """Pruned neighborhood over setup-removal moves.

    Movimiento elemental: apagar un setup existente y poder restaurarlo exactamente
    con undo. Se propone el movimiento para cualquier setup activo, manteniendo la
    idea de eliminar setups potencialmente redundantes.
    """

    def __init__(self, problem, lookback_limit=999):
        self.problem = problem
        self.lookback_limit = int(lookback_limit)

    def moves(self, sol):
        n_items = self.problem.inst.n_items
        n_periods = self.problem.inst.n_periods
        limit = max(0, min(self.lookback_limit, n_periods - 1))

        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue

                prev_setup_t = -1
                start = max(0, t - limit)
                for k in range(t - 1, start - 1, -1):
                    if sol[i][k]:
                        prev_setup_t = k
                        break

                yield (i, t, prev_setup_t)

    def apply(self, sol, m):
        i, t, _prev_t = m
        s = [list(row) for row in sol]
        s[i][t] = False
        return tuple(tuple(row) for row in s)

    def undo(self, sol, m):
        i, t, _prev_t = m
        s = [list(row) for row in sol]
        s[i][t] = True
        return tuple(tuple(row) for row in s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return RedundantSetupPruner(problem, **params)
