from random import Random
from typing import Any

COMPONENT = {
    "name": "item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.variable_groups"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class ItemChainDestruction:
    """Libera un ítem completo a lo largo de una cadena de períodos consecutivos."""

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst
        self._groups = problem.variable_groups(self.inst)

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        target_items = max(1, int(round(ratio * n_items)))
        chain_len = max(1, int(round(ratio * n_periods)))

        # Preferimos ítems con patrones más "fragmentados" (más cambios de setup)
        scores = []
        for i in range(n_items):
            row = sol[i]
            changes = sum(1 for t in range(1, n_periods) if row[t] != row[t - 1])
            active = sum(1 for t in range(n_periods) if row[t])
            scores.append((changes + 0.1 * active, i))
        scores.sort(reverse=True)

        chosen_items = [i for _, i in scores[:target_items]]
        free_vars: set[str] = set()

        for i in chosen_items:
            if n_periods <= chain_len:
                periods = list(range(n_periods))
            else:
                start = rng.randrange(0, n_periods - chain_len + 1)
                periods = list(range(start, start + chain_len))
            rng.shuffle(periods)
            for t in periods:
                free_vars.add(f"y_{i}_{t}")

        if not free_vars:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            free_vars.add(f"y_{i}_{t}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return ItemChainDestruction(problem)
