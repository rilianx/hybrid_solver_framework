COMPONENT = {
    "name": "adjacent_setup_drop",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {},
}

from examples.lotsizing.problem_model import LotSizingModel


class AdjacentSetupDrop:
    """Elimina un setup redundante en t si el ítem ya se preparó en t-1.
    Movimiento = (i, t).
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        inst = self.problem.inst
        for i in range(inst.n_items):
            for t in range(1, inst.n_periods):
                if sol[i][t] and sol[i][t - 1]:
                    yield (i, t)

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple((val if tt != t or ii != i else False) for tt, val in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        i, t = m
        return tuple(
            tuple((val if tt != t or ii != i else True) for tt, val in enumerate(row))
            for ii, row in enumerate(sol)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return AdjacentSetupDrop(problem)
