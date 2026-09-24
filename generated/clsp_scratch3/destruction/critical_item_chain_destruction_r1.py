from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name


COMPONENT = {
    "name": "critical_item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups", "problem.inst"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "chain_radius": {"type": "int", "range": [0, 4]},
    },
}


class CriticalItemChainDestruction:
    """Libera todos los setups de uno o pocos ítems críticos y una vecindad temporal alrededor."""

    def __init__(self, problem, inst, chain_radius: int = 1):
        self.problem = problem
        self.inst = inst
        self.chain_radius = chain_radius

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        item_score = []
        for i in range(n_items):
            setups = [t for t in range(n_periods) if sol[i][t]]
            if setups:
                # ítems con setups dispersos y costo alto son buenos candidatos para reconfigurar
                spread = setups[-1] - setups[0] + 1
                score = self.inst.setup_cost[i] / max(1.0, len(setups)) + 0.25 * spread
            else:
                score = 0.0
            item_score.append((score, i))
        item_score.sort(reverse=True)

        free_vars: set[str] = set()
        chosen_items = [i for _, i in item_score[: max(1, min(n_items, max(1, k // max(1, n_periods // 2))))]]

        for i in chosen_items:
            for t in range(n_periods):
                if sol[i][t]:
                    free_vars.add(var_name(i, t))
                    for dt in range(1, self.chain_radius + 1):
                        if t - dt >= 0:
                            free_vars.add(var_name(i, t - dt))
                        if t + dt < n_periods:
                            free_vars.add(var_name(i, t + dt))
                if len(free_vars) >= k:
                    break
            if len(free_vars) >= k:
                break

        # Si aún faltan variables, ampliar con el mismo ítem o vecinos aleatorios.
        while len(free_vars) < k:
            i = rng.choice(chosen_items) if chosen_items else rng.randrange(n_items)
            t = rng.randrange(n_periods)
            free_vars.add(var_name(i, t))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, chain_radius: int = 1):
    return CriticalItemChainDestruction(problem, problem.inst, chain_radius=chain_radius)
