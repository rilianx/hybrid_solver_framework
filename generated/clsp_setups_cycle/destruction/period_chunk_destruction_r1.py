from random import Random
from typing import Any

COMPONENT = {
    "name": "period_chunk_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "window_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class PeriodChunkDestruction:
    """Libera bloques de períodos completos, favoreciendo ventanas contiguas de tiempo."""

    def __init__(self, problem, ratio: float, window_bias: float):
        self.problem = problem
        self.ratio = float(ratio)
        self.window_bias = float(window_bias)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        vars_ = list(assignment.keys())
        if not vars_:
            return {}, set()

        target = max(1, min(len(vars_), int(round(max(0.0, ratio) * len(vars_)))))

        periods = list(range(n_periods))
        if n_periods == 1:
            chosen_periods = {0}
        else:
            # Ventana contigua preferida; si no alcanza, se completa con períodos aleatorios.
            window_len = max(1, min(n_periods, int(round((0.25 + 0.5 * self.window_bias) * n_periods))))
            start = rng.randrange(0, n_periods - window_len + 1)
            chosen_periods = set(range(start, start + window_len))
            while len(chosen_periods) * n_items < target and len(chosen_periods) < n_periods:
                p = rng.choice(periods)
                chosen_periods.add(p)

        free_vars = {f"y_{i}_{t}" for i in range(n_items) for t in chosen_periods if f"y_{i}_{t}" in assignment}

        if len(free_vars) < target:
            remaining = [v for v in vars_ if v not in free_vars]
            need = min(len(remaining), target - len(free_vars))
            if need > 0:
                free_vars |= set(rng.sample(remaining, need))

        if len(free_vars) >= len(vars_):
            keep = rng.choice(vars_)
            free_vars.remove(keep)

        partial = {v: assignment[v] for v in vars_ if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, window_bias: float = 0.7):
    return PeriodChunkDestruction(problem, ratio, window_bias)
