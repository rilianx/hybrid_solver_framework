COMPONENT = {
    "name": "drop_redundant_late_setup",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class DropRedundantLateSetup:
    """Elimina un setup tardío de un ítem cuando ya existe un setup previo contiguo.
    Movimiento = (i, t). Aplica: sol[i][t] := False.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def moves(self, sol):
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        for i in range(n_items):
            for t in range(1, n_periods):
                if sol[i][t] and sol[i][t - 1]:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple((sol[ii][tt] if (ii != i or tt != t) else False) for tt in range(self.inst.n_periods))
            for ii in range(self.inst.n_items)
        )

    def undo(self, sol, m):
        i, t = m
        return tuple(
            tuple((sol[ii][tt] if (ii != i or tt != t) else True) for tt in range(self.inst.n_periods))
            for ii in range(self.inst.n_items)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return DropRedundantLateSetup(problem)
