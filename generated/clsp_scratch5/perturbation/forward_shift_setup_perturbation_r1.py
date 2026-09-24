from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "forward_shift_setup_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class ForwardShiftSetupPerturbation:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items = inst.n_items
        n_periods = inst.n_periods
        s = [list(row) for row in sol]

        # Operador estructural: mover setups hacia delante o hacia atrás en el tiempo.
        # Busca ítems con setups múltiples y desplaza uno de sus setups a un período vecino.
        n_moves = max(1, int(round(strength)))
        moved = False

        items = list(range(n_items))
        rng.shuffle(items)

        for i in items:
            setup_periods = [t for t in range(n_periods) if s[i][t]]
            if len(setup_periods) < 2:
                continue

            for _ in range(min(n_moves, len(setup_periods))):
                t = rng.choice(setup_periods)
                candidates = []
                if t > 0:
                    candidates.append(t - 1)
                if t + 1 < n_periods:
                    candidates.append(t + 1)
                if not candidates:
                    continue
                t2 = rng.choice(candidates)
                if t2 == t:
                    continue
                # desplazar: apagar en t y encender en t2
                s[i][t] = False
                s[i][t2] = True
                moved = True
                setup_periods = [tt for tt in range(n_periods) if s[i][tt]]

        if not moved:
            # Fallback: mover cualquier setup a un vecino temporal.
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            t2 = t - 1 if (t > 0 and (t == n_periods - 1 or rng.random() < 0.5)) else min(n_periods - 1, t + 1)
            if t2 == t:
                t2 = (t + 1) % n_periods
            s[i][t] = not s[i][t]
            s[i][t2] = not s[i][t2]
            if not any(any(row) for row in s):
                s[i][t2] = True

        new_sol = tuple(tuple(row) for row in s)
        if new_sol == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s = [list(row) for row in sol]
            s[i][t] = not s[i][t]
            new_sol = tuple(tuple(row) for row in s)
        return new_sol


def build_component(problem, **params):
    return ForwardShiftSetupPerturbation(problem)
