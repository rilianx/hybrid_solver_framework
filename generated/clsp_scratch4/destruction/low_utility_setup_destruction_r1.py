from random import Random
from typing import Any

COMPONENT = {
    "name": "low_utility_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "noise": {"type": "float", "range": [0.0, 1.0]},
    },
}


class LowUtilitySetupDestruction:
    """Libera setups con baja utilidad aparente: poco costo evitado por unidad de tiempo de setup."""

    def __init__(self, problem, inst, noise: float = 0.15):
        self.problem = problem
        self.inst = inst
        self.noise = noise

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        # Utilidad aproximada: setup_cost por unidad de setup_time, ajustada por un
        # término simple de demanda futura cubierta si el setup ocurre en ese período.
        scored = []
        for i in range(n_items):
            st = max(self.inst.setup_time[i], 1e-9)
            base = self.inst.setup_cost[i] / st
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                future_demand = sum(self.inst.demand[i][tt] for tt in range(t, n_periods))
                # Menor score = menos útil mantener el setup.
                score = base - 0.01 * future_demand + self.noise * (rng.random() - 0.5)
                scored.append((score, rng.random(), i, t))

        scored.sort()  # menor utilidad primero

        free_vars: set[str] = set()
        for _, __, i, t in scored:
            free_vars.add(f"y_{i}_{t}")
            if len(free_vars) >= k:
                break

        # Garantiza al menos una variable liberada.
        if not free_vars:
            for i in range(n_items):
                for t in range(n_periods):
                    if sol[i][t]:
                        free_vars.add(f"y_{i}_{t}")
                        break
                if free_vars:
                    break
        if not free_vars:
            free_vars.add("y_0_0")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, noise: float = 0.15):
    return LowUtilitySetupDestruction(problem, problem.inst, noise=noise)
