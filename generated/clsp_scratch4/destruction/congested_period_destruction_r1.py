from random import Random
from typing import Any

COMPONENT = {
    "name": "congested_period_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "window_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CongestedPeriodDestruction:
    """Libera setups en los períodos más cargados para que el LNS redistribuya capacidad."""

    def __init__(self, problem, inst, window_bias: float = 0.35):
        self.problem = problem
        self.inst = inst
        self.window_bias = window_bias

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        load = []
        for t in range(n_periods):
            used = 0.0
            for i in range(n_items):
                if sol[i][t]:
                    used += self.inst.setup_time[i]
            load.append((used / max(self.inst.capacity[t], 1e-9), t))
        load.sort(reverse=True)

        free_vars: set[str] = set()
        chosen_periods = [t for _, t in load[: max(1, min(n_periods, int(round(1 + self.window_bias * n_periods))))]]
        if not chosen_periods:
            chosen_periods = [max(range(n_periods), key=lambda t: load[t][0])]

        # Prioriza los setups de períodos congestionados, con un pequeño sesgo aleatorio.
        candidates = []
        for t in chosen_periods:
            for i in range(n_items):
                if sol[i][t]:
                    candidates.append((load[t][0], rng.random(), i, t))
        candidates.sort(reverse=True)

        for _, __, i, t in candidates:
            if len(free_vars) >= k:
                break
            free_vars.add(f"y_{i}_{t}")

        # Si todavía no alcanza, completa con variables de los períodos más cargados.
        if len(free_vars) < k:
            for _, t in load:
                for i in range(n_items):
                    name = f"y_{i}_{t}"
                    if name in free_vars:
                        continue
                    free_vars.add(name)
                    if len(free_vars) >= k:
                        break
                if len(free_vars) >= k:
                    break

        if not free_vars:
            t = load[0][1] if load else 0
            i = 0
            free_vars.add(f"y_{i}_{t}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, window_bias: float = 0.35):
    return CongestedPeriodDestruction(problem, problem.inst, window_bias=window_bias)
