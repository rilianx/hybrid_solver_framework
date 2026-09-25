from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "low_value_item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "focus_top_k": {"type": "int", "range": [1, 5]},
    },
}


class LowValueItemChainDestruction:
    """Libera todos los setups de uno o más ítems con peor utilidad económica."""

    def __init__(self, problem, inst, focus_top_k: int = 2):
        self.problem = problem
        self.inst = inst
        self.focus_top_k = max(1, int(focus_top_k))

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods

        item_score = []
        for i in range(n_items):
            setups = sum(1 for t in range(n_periods) if sol[i][t])
            demand = sum(float(self.inst.demand[i][t]) for t in range(n_periods))
            setup_cost = float(self.inst.setup_cost[i])
            holding_cost = float(self.inst.holding_cost[i])
            # Ítems caros de setup y con demanda pequeña son buenos candidatos a reestructurar.
            score = (setup_cost + 1.0) / (demand + 1.0) + 0.25 * holding_cost
            item_score.append((score, -setups, i))

        item_score.sort(reverse=True)
        chosen_items = [i for _, _, i in item_score[: min(self.focus_top_k, n_items)]]

        free_vars: set[str] = set()
        for var_name in assignment:
            # Las variables del CLSP son setups binarios y siguen el patrón y_{i}_{t}.
            # Liberamos todos los períodos de los ítems seleccionados.
            parts = var_name.split("_")
            if len(parts) >= 3 and parts[0] == "y":
                try:
                    item_idx = int(parts[1])
                except ValueError:
                    continue
                if item_idx in chosen_items:
                    free_vars.add(var_name)

        target_k = max(1, int(round(ratio * len(assignment))))
        if len(free_vars) < target_k:
            remaining = [v for v in assignment if v not in free_vars]
            rng.shuffle(remaining)
            free_vars.update(remaining[: target_k - len(free_vars)])
        elif len(free_vars) > target_k:
            picked = list(free_vars)
            rng.shuffle(picked)
            free_vars = set(picked[:target_k])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.20, focus_top_k: int = 2):
    return LowValueItemChainDestruction(problem, problem.inst, focus_top_k=focus_top_k)
