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
        for i1 in range(n_items):
            row1 = sol[i1]
            for t1 in range(n_periods):
                if not row1[t1]:
                    continue
                for i2 in range(n_items):
                    row2 = sol[i2]
                    for t2 in range(n_periods):
                        if row2[t2]:
                            continue
                        if i1 != i2 or t1 != t2:
                            yield (i1, t1, i2, t2)

    def apply(self, sol, m):
        i1, t1, i2, t2 = m
        s = [list(row) for row in sol]
        s[i1][t1] = False
        s[i2][t2] = True
        return self.problem.parts.canonical(tuple(tuple(row) for row in s))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CrossItemPeriodSwapNeighborhood(problem)
