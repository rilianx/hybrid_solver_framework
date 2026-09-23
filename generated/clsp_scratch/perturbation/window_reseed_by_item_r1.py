from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "window_reseed_by_item",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 5.0]},
    },
}


class WindowReseedByItem:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        s = [list(row) for row in sol]

        k = max(1, int(round(strength)))
        items_to_reseed = min(n_items, k)

        # Destrucción estructural: selecciona ítems completos y vuelve a sembrar
        # sus setups en una ventana de períodos, creando patrones no triviales.
        items = list(range(n_items))
        rng.shuffle(items)
        selected_items = items[:items_to_reseed]

        for i in selected_items:
            current = [t for t in range(n_periods) if s[i][t]]
            if not current:
                # Si el ítem no tiene setups, sembrar uno.
                t = rng.randrange(n_periods)
                s[i][t] = True
                continue

            # Mantener 1..m setups, pero moverlos a una ventana aleatoria.
            w = max(1, min(n_periods, 1 + int(rng.random() * k)))
            start = rng.randrange(0, n_periods - w + 1)
            window = list(range(start, start + w))

            # Apagar todos los setups del ítem y reinsertar algunos dentro de la ventana.
            for t in current:
                s[i][t] = False

            m = min(len(current), w)
            chosen = rng.sample(window, m)
            for t in chosen:
                s[i][t] = True

        # Garantía adicional: si por alguna razón no cambió, flip en una celda aleatoria.
        if tuple(tuple(row) for row in s) == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return WindowReseedByItem(problem)
