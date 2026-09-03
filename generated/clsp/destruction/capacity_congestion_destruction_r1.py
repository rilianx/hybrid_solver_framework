from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "capacity_congestion_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
    },
}


class CapacityCongestionDestruction:
    """Libera setups en los períodos más cargados, para reoptimizar la congestión local."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        target = max(1, int(round(ratio * total_vars)))

        load_by_t = []
        for t in range(n_periods):
            load = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    load += self.inst.setup_time[i]
            load_by_t.append((load / max(self.inst.capacity[t], 1e-9), t))
        load_by_t.sort(reverse=True)

        free_vars = set()
        for _, t in load_by_t:
            period_vars = [var_name(i, t) for i in range(n_items)]
            rng.shuffle(period_vars)
            for v in period_vars:
                free_vars.add(v)
                if len(free_vars) >= target:
                    break
            if len(free_vars) >= target:
                break

        if not free_vars:
            t = rng.randrange(n_periods)
            free_vars.add(var_name(rng.randrange(n_items), t))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return CapacityCongestionDestruction(problem, problem.inst)
