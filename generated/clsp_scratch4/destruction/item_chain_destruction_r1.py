from random import Random
from typing import Any

COMPONENT = {
    "name": "item_chain_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "chain_length": {"type": "int", "range": [1, 12]},
    },
}


class ItemChainDestruction:
    """Libera todas las decisiones de uno o varios ítems para rehacer su cadena temporal completa."""

    def __init__(self, problem, inst, chain_length: int = 2):
        self.problem = problem
        self.inst = inst
        self.chain_length = chain_length

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods
        total_vars = n_items * n_periods
        k = max(1, int(round(ratio * total_vars)))

        # Selecciona ítems con muchos setups o con setups costosos.
        item_score = []
        for i in range(n_items):
            active = sum(1 for t in range(n_periods) if sol[i][t])
            score = active * self.inst.setup_cost[i]
            item_score.append((score, rng.random(), i))
        item_score.sort(reverse=True)

        free_vars: set[str] = set()
        chosen_items = []
        max_items = max(1, min(n_items, self.chain_length))
        for _, __, i in item_score[:max_items]:
            chosen_items.append(i)

        # Libera ítems completos hasta alcanzar la cuota.
        for i in chosen_items:
            for t in range(n_periods):
                free_vars.add(f"y_{i}_{t}")
            if len(free_vars) >= k:
                break

        # Si sobra o falta, añade períodos aleatorios de esos ítems primero.
        if len(free_vars) < k:
            for i in chosen_items:
                periods = list(range(n_periods))
                rng.shuffle(periods)
                for t in periods:
                    free_vars.add(f"y_{i}_{t}")
                    if len(free_vars) >= k:
                        break
                if len(free_vars) >= k:
                    break

        # Si aún falta, completa con setups activos de otros ítems.
        if len(free_vars) < k:
            active_vars = [(rng.random(), i, t) for i in range(n_items) for t in range(n_periods) if sol[i][t]]
            active_vars.sort()
            for _, i, t in active_vars:
                free_vars.add(f"y_{i}_{t}")
                if len(free_vars) >= k:
                    break

        if not free_vars:
            free_vars.add("y_0_0")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2, chain_length: int = 2):
    return ItemChainDestruction(problem, problem.inst, chain_length=chain_length)
