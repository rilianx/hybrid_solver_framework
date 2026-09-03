from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "period_window_rewire",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
        "window_frac": {"type": "float", "range": [0.1, 1.0]},
    },
}


class PeriodWindowRewire:
    def __init__(self, problem, window_frac: float = 0.35):
        self.problem = problem
        self.inst = problem.inst
        self.window_frac = window_frac

    def _copy_sol(self, sol):
        return tuple(tuple(row) for row in sol)

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_periods == 0:
            return sol

        w = max(1, min(n_periods, int(round(self.window_frac * max(1.0, strength)))))
        start = rng.randrange(n_periods)
        periods = [(start + k) % n_periods for k in range(w)]

        out = [list(row) for row in sol]

        # Destruye patrones dentro de una ventana: quita setups "redundantes"
        # y, si queda vacía alguna fila en la ventana, fuerza al menos un setup
        # por ítem en un período seleccionado aleatoriamente dentro de la ventana.
        changed = False
        for i in range(n_items):
            active = [t for t in periods if sol[i][t]]
            if active and rng.random() < 0.5:
                # apaga uno o más setups en la ventana
                k = max(1, min(len(active), int(round(0.5 * strength))))
                for t in rng.sample(active, k):
                    out[i][t] = False
                    changed = True

        # Reinyecta algunos setups en la ventana para mover carga temporalmente
        for i in range(n_items):
            if not any(out[i][t] for t in periods):
                t = rng.choice(periods)
                out[i][t] = True
                changed = True

        # Pequeño "rewire": desplaza setups dentro de la ventana hacia un vecino
        for i in range(n_items):
            active = [t for t in periods if out[i][t]]
            if active and rng.random() < 0.35:
                t = rng.choice(active)
                candidates = [p for p in periods if p != t]
                if candidates:
                    u = rng.choice(candidates)
                    out[i][t] = False
                    out[i][u] = True
                    changed = True

        if not changed:
            i = rng.randrange(n_items)
            t = rng.choice(periods)
            out[i][t] = not out[i][t]

        return tuple(tuple(row) for row in out)


def build_component(problem, **params):
    window_frac = float(params.get("window_frac", 0.35))
    return PeriodWindowRewire(problem, window_frac=window_frac)
