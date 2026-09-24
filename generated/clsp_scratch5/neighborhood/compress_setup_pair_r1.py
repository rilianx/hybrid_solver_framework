COMPONENT = {
    "name": "compress_setup_pair",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class CompressSetupPair:
    """Elimina dos setups consecutivos de un mismo ítem cuando ya hay un setup previo.
    Movimiento = (i, t). Aplica: sol[i][t] := False y sol[i][t+1] := False.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(1, n_periods - 1):
                if sol[i][t] and sol[i][t + 1] and sol[i][t - 1]:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (sol[ii][tt] if (ii != i or tt not in (t, t + 1)) else False)
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def undo(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (sol[ii][tt] if (ii != i or tt not in (t, t + 1)) else True)
                for tt in range(self.inst.n_periods)
            )
            for ii in range(self.inst.n_items)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CompressSetupPair(problem)
