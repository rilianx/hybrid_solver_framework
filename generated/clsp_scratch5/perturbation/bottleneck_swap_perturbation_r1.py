from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "bottleneck_swap_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class BottleneckSwapPerturbation:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        s = [list(row) for row in sol]

        # Idea distinta: concentrar el kick en períodos "cuello de botella" y
        # reasignar setups entre ítems dentro de esos períodos.
        loads = []
        for t in range(n_periods):
            load = sum(inst.setup_time[i] for i in range(n_items) if s[i][t])
            loads.append(load / inst.capacity[t] if inst.capacity[t] else 0.0)

        # Selecciona los períodos más cargados.
        m = max(1, min(n_periods, int(round(strength))))
        hot_periods = sorted(range(n_periods), key=lambda t: loads[t], reverse=True)[:m]

        changed = False
        for t in hot_periods:
            on_items = [i for i in range(n_items) if s[i][t]]
            off_items = [i for i in range(n_items) if not s[i][t]]
            if not on_items or not off_items:
                continue

            # Intercambio: apaga un setup de un ítem "caro" en el período caliente
            # y enciende uno distinto para cambiar la composición del período.
            i_off = rng.choice(on_items)
            i_on = rng.choice(off_items)
            s[i_off][t] = False
            s[i_on][t] = True
            changed = True

            # Con strength alto, intenta además mover el setup apagado a un período vecino.
            if strength >= 3.0:
                neigh = []
                if t > 0:
                    neigh.append(t - 1)
                if t + 1 < n_periods:
                    neigh.append(t + 1)
                if neigh:
                    t2 = rng.choice(neigh)
                    if not s[i_off][t2]:
                        s[i_off][t2] = True
                        changed = True

        if not changed:
            # Fallback robusto: intercambio simple en cualquier período.
            t = rng.randrange(n_periods)
            i1 = rng.randrange(n_items)
            i2 = (i1 + 1 + rng.randrange(max(1, n_items - 1))) % n_items
            s[i1][t], s[i2][t] = s[i2][t], s[i1][t]
            if s == [list(row) for row in sol]:
                s[i1][t] = not s[i1][t]

        new_sol = tuple(tuple(row) for row in s)
        if new_sol == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[i][t] = not s[i][t]
            new_sol = tuple(tuple(row) for row in s)
        return new_sol


def build_component(problem, **params):
    return BottleneckSwapPerturbation(problem)
