from generated.clsp_setups_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "single_setup_toggle",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class SingleSetupToggle:
    """Abre o cierra el setup de un único (ítem, período). Movimiento = (i, t)."""

    def __init__(self, problem):
        self.problem = problem
        self.n = problem.inst.n_items
        self.T = problem.inst.n_periods

    def moves(self, sol):
        for i in range(self.n):
            for t in range(self.T):
                yield (i, t)

    def apply(self, sol, m):
        i, t = m
        plan = [list(r) for r in canonical(sol)]
        plan[i][t] = not plan[i][t]
        return canonical(plan)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem):
    return SingleSetupToggle(problem)
