from random import Random
from typing import Any

COMPONENT = {
    "name": "low_leverage_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class LowLeverageSetupDestruction:
    """Libera setups con menor 'apalancamiento': ítems caros/tiempo-intensivos en períodos con poca demanda local."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        k = max(1, int(round(ratio * n_items * n_periods)))

        candidates = []
        for i in range(n_items):
            for t in range(n_periods):
                if not sol[i][t]:
                    continue
                local_demand = sum(self.inst.demand[j][t] for j in range(n_items))
                leverage = (self.inst.setup_cost[i] + 1.0) / (1.0 + self.inst.setup_time[i] + local_demand)
                # Menor leverage => más fácil de destruir
                candidates.append((leverage, i, t))

        candidates.sort(key=lambda x: x[0])

        free_vars: set[str] = set()
        for _, i, t in candidates:
            free_vars.add(f"y_{i}_{t}")
            if len(free_vars) >= k:
                break

        # Si aún faltan variables, completamos con setups aleatorios activos.
        if len(free_vars) < k:
            active = [(i, t) for i in range(n_items) for t in range(n_periods) if sol[i][t]]
            rng.shuffle(active)
            for i, t in active:
                free_vars.add(f"y_{i}_{t}")
                if len(free_vars) >= k:
                    break

        if not free_vars:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            free_vars.add(f"y_{i}_{t}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25):
    return LowLeverageSetupDestruction(problem)
