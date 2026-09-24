from __future__ import annotations

import math
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
    """Libera setups completos de uno o varios ítems en bloques temporales.
    La cantidad de variables liberadas crece monótonamente con `ratio`.
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

        free_vars: set[str] = set()
        if n_items <= 0 or n_periods <= 0:
            return dict(assignment), free_vars

        # Número de ítems a atacar: crece con la ratio.
        k_items = max(1, math.ceil(max(0.0, ratio) * n_items * self.item_fraction))
        k_items = min(n_items, k_items)

        items = list(range(n_items))
        rng.shuffle(items)
        chosen_items = items[:k_items]

        # Total de variables a liberar: monótono en ratio.
        target_free = max(1, math.ceil(max(0.0, ratio) * n_items * n_periods * self.item_fraction))
        target_free = min(n_items * n_periods, target_free)

        # Reparto por ítems: el primero recibe el bloque principal.
        remaining = target_free
        for idx, i in enumerate(chosen_items):
            if remaining <= 0:
                break

            if idx == 0 and ratio >= 0.5:
                # Para ratios altas, destruye el horizonte completo del ítem ancla.
                periods_to_free = min(n_periods, remaining)
            else:
                # Bloque contiguo cuyo tamaño también crece con la ratio.
                base = max(1, math.ceil(max(0.0, ratio) * n_periods * (0.5 + 0.5 * self.item_fraction)))
                periods_to_free = min(n_periods, min(remaining, base))

            if periods_to_free >= n_periods:
                for t in range(n_periods):
                    free_vars.add(var_name(i, t))
                remaining -= n_periods
                continue

            start_max = max(0, n_periods - periods_to_free)
            start = rng.randrange(start_max + 1) if start_max > 0 else 0
            end = start + periods_to_free
            for t in range(start, end):
                free_vars.add(var_name(i, t))
            remaining -= periods_to_free

        # Si aún faltan variables por liberar, completamos con períodos adicionales
        # de los ítems seleccionados, manteniendo el patrón por bloques.
        if remaining > 0:
            for i in chosen_items:
                if remaining <= 0:
                    break
                already = [t for t in range(n_periods) if var_name(i, t) in free_vars]
                if len(already) >= n_periods:
                    continue
                add = min(remaining, n_periods - len(already))
                for t in range(n_periods):
                    if add <= 0:
                        break
                    v = var_name(i, t)
                    if v not in free_vars:
                        free_vars.add(v)
                        add -= 1
                        remaining -= 1

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(
    problem,
    ratio: float = 0.25,
    item_fraction: float = 0.4,
    full_horizon_prob: float = 0.25,
):
    return DestroyItemBlock(
        problem,
        problem.inst,
        item_fraction=item_fraction,
        full_horizon_prob=full_horizon_prob,
    )
