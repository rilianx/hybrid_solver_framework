COMPONENT = {
    "name": "cross_item_period_swap",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}


class CrossItemPeriodSwapNeighborhood:
    """Intercambia el estado de setup entre dos ítems en un período dado: (i1, i2, t)."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for t in range(n_periods):
            for i1 in range(n_items):
                for i2 in range(i1 + 1, n_items):
                    if sol[i1][t] != sol[i2][t]:
                        yield (i1, i2, t)

    def apply(self, sol, m):
        i1, i2, t = m
        s = [list(row) for row in sol]
        s[i1][t], s[i2][t] = s[i2][t], s[i1][t]
        return self.problem.parts.canonical(tuple(tuple(row) for row in s))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CrossItemPeriodSwapNeighborhood(problem)
