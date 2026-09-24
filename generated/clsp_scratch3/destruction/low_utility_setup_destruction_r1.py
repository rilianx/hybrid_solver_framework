from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "low_utility_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "noise": {"type": "float", "range": [0.0, 0.5]},
    },
}


class LowUtilitySetupDestruction:
    """Libera setups que parecen menos útiles: poco ahorro de inventario frente a costo de setup."""

    def __init__(self, problem, inst, noise: float = 0.15):
        self.problem = problem
        self.inst = inst
        self.noise = noise

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        scored = []
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                future_demand = sum(self.inst.demand[i][tt] for tt in range(t, n_periods))
                # Heurística simple: setups con demanda futura baja y costo de setup alto son menos valiosos.
                utility = future_demand / max(1.0, self.inst.setup_cost[i])
                utility += self.noise * rng.random()
                scored.append((utility, i, t))

        scored.sort(key=lambda x: x[0])  # menor utilidad primero
        free_vars: set[str] = set()

        for _, i, t in scored:
            free_vars.add(var_name(i, t))
            if len(free_vars) >= k:
                break

        # Si no hay suficientes setups activos, completar con variables aleatorias.
        while len(free_vars) < k:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            free_vars.add(var_name(i, t))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, noise: float = 0.15):
    return LowUtilitySetupDestruction(problem, problem.inst, noise=noise)
