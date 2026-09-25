from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "congestion_window_shuffle",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "window_size": {"type": "int", "range": [1, 6]},
        "drop_rate": {"type": "float", "range": [0.1, 1.0]},
    },
}


class CongestionWindowShufflePerturbation:
    def __init__(self, problem, window_size: int = 2, drop_rate: float = 0.5):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.window_size = max(1, int(window_size))
        self.drop_rate = max(0.1, min(1.0, float(drop_rate)))

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        w = max(1, min(n_periods, int(round(self.window_size * max(1.0, strength)))))
        start = rng.randrange(0, n_periods - w + 1)
        end = start + w
        cand = [list(row) for row in sol]

        # Destruir una fracción de setups dentro de la ventana.
        window_positions = [(i, t) for i in range(n_items) for t in range(start, end)]
        rng.shuffle(window_positions)
        to_drop = max(1, int(round(len(window_positions) * self.drop_rate * min(1.0, strength / 3.0))))
        dropped = window_positions[:to_drop]
        for i, t in dropped:
            cand[i][t] = False

        # Reconstrucción: mover algunos setups a períodos vecinos aleatorios.
        for i, t in dropped:
            if rng.random() < 0.65:
                choices = []
                if t > 0:
                    choices.append(t - 1)
                choices.append(t)
                if t + 1 < n_periods:
                    choices.append(t + 1)
                tt = rng.choice(choices)
                cand[i][tt] = True

        # Garantizar cambio efectivo.
        sol2 = tuple(tuple(row) for row in cand)
        if sol2 == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            cand[i][t] = not cand[i][t]
            sol2 = tuple(tuple(row) for row in cand)

        return sol2


def build_component(problem, window_size: int = 2, drop_rate: float = 0.5):
    return CongestionWindowShufflePerturbation(problem, window_size=window_size, drop_rate=drop_rate)
