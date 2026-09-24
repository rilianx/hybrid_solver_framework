from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "destroy_repair_window_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class DestroyRepairWindowPerturbation:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst

    def _copy_sol(self, sol):
        return tuple(tuple(bool(v) for v in row) for row in sol)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        s = [list(row) for row in sol]

        # Ventana de destrucción: elimina setups en un bloque corto y repone
        # algunos de ellos en posiciones elegidas aleatoriamente dentro de la ventana.
        w = max(1, min(n_periods, int(round(strength))))
        start = rng.randrange(0, max(1, n_periods - w + 1))
        window = list(range(start, min(n_periods, start + w)))

        changed = False

        # Apagar algunos setups dentro de la ventana.
        for t in window:
            on_items = [i for i in range(n_items) if s[i][t]]
            if not on_items:
                continue
            k_off = max(1, min(len(on_items), int(round(0.5 * strength))))
            for i in rng.sample(on_items, k_off):
                s[i][t] = False
                changed = True

        # Reinsertar setups, preferentemente en otros períodos dentro de la misma ventana.
        for t in window:
            off_items = [i for i in range(n_items) if not s[i][t]]
            if not off_items:
                continue
            # Con strength mayor, movemos más configuraciones hacia la ventana.
            k_on = max(0, min(len(off_items), int(strength // 2)))
            if k_on > 0:
                for i in rng.sample(off_items, k_on):
                    s[i][t] = True
                    changed = True

        if not changed:
            # Fallback: voltea un setup aleatorio si existe.
            candidates = [(i, t) for i in range(n_items) for t in range(n_periods)]
            i, t = rng.choice(candidates)
            s[i][t] = not s[i][t]
            if not any(any(row) for row in s):
                s[i][t] = True

        new_sol = tuple(tuple(row) for row in s)
        if new_sol == sol:
            i, t = rng.randrange(n_items), rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[i][t] = not s[i][t]
            new_sol = tuple(tuple(row) for row in s)
        return new_sol


def build_component(problem, **params):
    return DestroyRepairWindowPerturbation(problem)
