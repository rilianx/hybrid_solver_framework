from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "destroy_item_block",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.7]},
        "item_fraction": {"type": "float", "range": [0.1, 1.0]},
        "full_horizon_prob": {"type": "float", "range": [0.0, 1.0]},
    },
}


class DestroyItemBlock:
    """Libera setups completos de uno o varios ítems en una ventana temporal,
    o incluso en todo el horizonte para un ítem ancla.
    """

    def __init__(
        self,
        problem,
        inst,
        item_fraction: float = 0.4,
        full_horizon_prob: float = 0.25,
    ):
        self.problem = problem
        self.inst = inst
        self.item_fraction = item_fraction
        self.full_horizon_prob = full_horizon_prob

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        n_items = self.inst.n_items
        n_periods = self.inst.n_periods

        # Número de ítems a atacar: al menos uno, crece con la ratio.
        k_items = max(1, int(round(self.item_fraction * max(1.0, ratio * n_items))))
        k_items = min(n_items, k_items)

        items = list(range(n_items))
        rng.shuffle(items)
        chosen_items = items[:k_items]

        free_vars: set[str] = set()

        # Un ítem ancla puede quedar libre en todo el horizonte: destrucción radical.
        anchor = chosen_items[0]
        if n_periods > 0 and rng.random() < self.full_horizon_prob + 0.5 * ratio:
            for t in range(n_periods):
                free_vars.add(var_name(anchor, t))
        else:
            # Ventana contigua sobre el horizonte.
            window = max(1, int(round(ratio * n_periods)))
            window = min(n_periods, window)
            start_max = max(0, n_periods - window)
            start = rng.randrange(start_max + 1) if start_max > 0 else 0
            end = min(n_periods, start + window)
            for t in range(start, end):
                free_vars.add(var_name(anchor, t))

        # Ítems adicionales: liberamos bloques temporales más pequeños para perturbar
        # su política sin destruir todo el resto.
        for i in chosen_items[1:]:
            if n_periods == 0:
                continue
            if rng.random() < 0.5:
                # Bloque entero del ítem, pero normalmente más corto.
                window = max(1, int(round(max(1.0, ratio * n_periods * 0.5))))
                window = min(n_periods, window)
                start_max = max(0, n_periods - window)
                start = rng.randrange(start_max + 1) if start_max > 0 else 0
                end = min(n_periods, start + window)
                for t in range(start, end):
                    free_vars.add(var_name(i, t))
            else:
                # Algunos períodos dispersos del ítem.
                m = max(1, int(round(ratio * n_periods * 0.5)))
                chosen_t = set()
                while len(chosen_t) < m:
                    chosen_t.add(rng.randrange(n_periods))
                for t in chosen_t:
                    free_vars.add(var_name(i, t))

        # Garantía de liberación mínima y consistencia con el assignment.
        if not free_vars:
            free_vars.add(var_name(anchor, 0))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, item_fraction: float = 0.4, full_horizon_prob: float = 0.25):
    return DestroyItemBlock(problem, problem.inst, item_fraction=item_fraction, full_horizon_prob=full_horizon_prob)
