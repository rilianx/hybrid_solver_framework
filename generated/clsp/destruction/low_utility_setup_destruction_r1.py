from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "low_utility_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
    },
}


class LowUtilitySetupDestruction:
    """Libera setups que parecen aportar menos: altos costos y poca demanda futura cubierta."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _future_demand(self, i: int, t: int) -> float:
        return sum(self.inst.demand[i][tt] for tt in range(t, self.inst.n_periods))

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        target = max(1, int(round(ratio * total_vars)))

        scored = []
        for i in range(n_items):
            for t in range(n_periods):
                if sol[i][t]:
                    future = self._future_demand(i, t)
                    score = (self.inst.setup_cost[i] + 1.0) / (1.0 + future)
                    scored.append((score, i, t))
        scored.sort(reverse=True)

        free_vars = set()
        for _, i, t in scored:
            free_vars.add(var_name(i, t))
            if len(free_vars) >= target:
                break

        if len(free_vars) < target:
            candidates = [var_name(i, t) for i in range(n_items) for t in range(n_periods) if var_name(i, t) not in free_vars]
            rng.shuffle(candidates)
            for v in candidates:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break

        if not free_vars:
            free_vars.add(var_name(rng.randrange(n_items), rng.randrange(n_periods)))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return LowUtilitySetupDestruction(problem, problem.inst)
