from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "item_chain_merge_split",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 12.0]},
        "merge_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class ItemChainMergeSplit:
    def __init__(self, problem, merge_bias: float = 0.7):
        self.problem = problem
        self.inst = problem.inst
        self.merge_bias = merge_bias

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        out = [list(row) for row in sol]
        n_ops = max(1, int(round(strength)))

        for _ in range(n_ops):
            i = rng.randrange(n_items)
            active = [t for t in range(n_periods) if out[i][t]]
            inactive = [t for t in range(n_periods) if not out[i][t]]

            if len(active) >= 2 and rng.random() < self.merge_bias:
                # Fusión: elimina dos setups cercanos del mismo ítem y deja uno
                active.sort()
                idx = rng.randrange(len(active) - 1)
                t1, t2 = active[idx], active[idx + 1]
                # elige un período intermedio o el más temprano
                t_new = t1 if rng.random() < 0.5 else t2
                out[i][t1] = False
                out[i][t2] = False
                out[i][t_new] = True
            else:
                # Split: quita un setup y lo reubica a otro período
                if active and inactive:
                    t_old = rng.choice(active)
                    t_new = rng.choice(inactive)
                    out[i][t_old] = False
                    out[i][t_new] = True
                elif inactive:
                    # Si el ítem no tiene setups, crea un pequeño patrón
                    t_new = rng.choice(inactive)
                    out[i][t_new] = True
                elif active:
                    # Todos son True: apaga uno y enciende otro (casi seguro distinto)
                    t_old = rng.choice(active)
                    t_new = rng.randrange(n_periods)
                    while t_new == t_old and n_periods > 1:
                        t_new = rng.randrange(n_periods)
                    out[i][t_old] = False
                    out[i][t_new] = True

        # Garantiza cambio estructural si accidentalmente quedó igual
        new_sol = tuple(tuple(row) for row in out)
        if new_sol == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            out[i][t] = not out[i][t]
            new_sol = tuple(tuple(row) for row in out)
        return new_sol


def build_component(problem, **params):
    merge_bias = float(params.get("merge_bias", 0.7))
    return ItemChainMergeSplit(problem, merge_bias=merge_bias)
