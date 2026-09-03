COMPONENT = {
    "name": "adjacent_setup_drop",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {},
}

from examples.lotsizing.problem_model import LotSizingModel


class AdjacentSetupDrop:
    """Elimina un setup unitario.
    Prioriza setups redundantes 'adyacentes' del mismo ítem, pero garantiza
    que el vecindario no quede vacío cuando existen setups activados.
    Movimiento = (i, t).
    """

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        inst = self.problem.inst
        prioritized = []
        fallback = []
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                if not sol[i][t]:
                    continue
                move = (i, t)
                fallback.append(move)
                left = t > 0 and sol[i][t - 1]
                right = t + 1 < inst.n_periods and sol[i][t + 1]
                if left or right:
                    prioritized.append(move)

        if prioritized:
            for m in prioritized:
                yield m
        else:
            for m in fallback:
                yield m

    def apply(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (val if not (ii == i and tt == t) else False)
                for tt, val in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def undo(self, sol, m):
        i, t = m
        return tuple(
            tuple(
                (val if not (ii == i and tt == t) else True)
                for tt, val in enumerate(row)
            )
            for ii, row in enumerate(sol)
        )

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return AdjacentSetupDrop(problem)
