from math import ceil
from random import Random

from generated.clsp_setups_cycle.model.parts import canonical

COMPONENT = {
    "name": "period_window_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "item_fraction": {"type": "float", "range": [0.3, 1.0]},
    },
}


class PeriodWindowDestruction:
    """Libera y_{i,t} para un subconjunto de ítems en una ventana contigua de períodos.

    Capta la interacción por capacidad compartida dentro de los períodos y el
    acoplamiento temporal por inventario entre períodos consecutivos.
    """

    def __init__(self, problem, item_fraction: float = 0.7):
        self.problem = problem
        self.inst = problem.inst
        self.item_fraction = float(item_fraction)

    def destroy(self, sol, ratio: float, rng: Random):
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)
        keys = list(assignment.keys())
        n_items, n_periods = self.inst.n_items, self.inst.n_periods
        total = len(keys)
        k = min(total, max(1, int(round(ratio * total))))

        m = max(1, min(n_items, int(round(self.item_fraction * n_items))))
        items = rng.sample(range(n_items), m) if n_items > 0 else []
        w = max(1, min(n_periods, int(ceil(k / max(1, m)))))
        start = rng.randint(0, max(0, n_periods - w))

        free_vars = set()
        for i in items:
            for t in range(start, start + w):
                name = f"y_{i}_{t}"
                if name in assignment:
                    free_vars.add(name)

        # completar hasta k extendiendo la ventana a ítems no elegidos
        if len(free_vars) < k:
            rest = [f"y_{i}_{t}" for i in range(n_items) if i not in items
                    for t in range(start, start + w) if f"y_{i}_{t}" in assignment]
            rng.shuffle(rest)
            for name in rest:
                if len(free_vars) >= k:
                    break
                free_vars.add(name)
        if not free_vars:
            free_vars.add(rng.choice(keys))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, item_fraction: float = 0.7, **params):
    return PeriodWindowDestruction(problem, item_fraction=item_fraction)
