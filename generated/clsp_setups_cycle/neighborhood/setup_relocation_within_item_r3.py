COMPONENT = {
    "name": "setup_relocation_within_item",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.parts.canonical"],
    "params": {},
}


class SetupRelocationWithinItemNeighborhood:
    """Mueve un setup de un período a otro dentro del mismo ítem: (i, t_from, t_to)."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        for i in range(n_items):
            row = sol[i]
            true_periods = [t for t in range(n_periods) if row[t]]
            false_periods = [t for t in range(n_periods) if not row[t]]
            for t_from in true_periods:
                for t_to in false_periods:
                    if t_from != t_to:
                        yield (i, t_from, t_to)

    def apply(self, sol, m):
        i, t_from, t_to = m
        s = [list(row) for row in sol]
        s[i][t_from] = False
        s[i][t_to] = True
        return self.problem.parts.canonical(tuple(tuple(row) for row in s))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return SetupRelocationWithinItemNeighborhood(problem)
