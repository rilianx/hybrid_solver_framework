from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "period_saturation_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class PeriodSaturationDestruction:
    """Libera setups en los períodos más congestionados, con algo de aleatoriedad."""

    def __init__(self, problem, inst, bias: float = 0.35):
        self.problem = problem
        self.inst = inst
        self.bias = bias

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        groups = self.problem.variable_groups(self.inst)
        period_keys = sorted(groups.keys(), key=lambda key: int(key[1:]))
        period_loads = []
        for key in period_keys:
            t = int(key[1:])
            load = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    load += self.inst.setup_time[i]
            period_loads.append((load, t))

        period_loads.sort(reverse=True)
        chosen: set[str] = set()

        for _, t in period_loads:
            vars_t = [var_name(i, t) for i in range(n_items)]
            if rng.random() < self.bias:
                vars_t.sort(key=lambda v: (-assignment[v], rng.random()))
            else:
                rng.shuffle(vars_t)
            for v in vars_t:
                if v not in chosen:
                    chosen.add(v)
                    if len(chosen) >= k:
                        break
            if len(chosen) >= k:
                break

        while len(chosen) < k:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            chosen.add(var_name(i, t))

        free_vars = chosen
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, bias: float = 0.35):
    return PeriodSaturationDestruction(problem, problem.inst, bias=bias)
