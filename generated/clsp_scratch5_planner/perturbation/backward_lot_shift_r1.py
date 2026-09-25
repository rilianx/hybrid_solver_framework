from __future__ import annotations

from random import Random
from typing import List, Tuple

COMPONENT = {
    "name": "backward_lot_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "int", "range": [1, 5]},
    },
}


class BackwardLotShift:
    """Kick que consolida lotes de un único ítem desplazando setups hacia atrás."""

    def __init__(self, problem, strength: int = 1):
        self.problem = problem
        self.strength = max(1, int(strength))

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        n_items = inst.n_items
        n_periods = inst.n_periods

        y: List[List[bool]] = [list(row) for row in sol]
        moves = max(1, int(round(strength)))

        for _ in range(moves):
            candidates: List[Tuple[int, int]] = []
            for i in range(n_items):
                periods = [t for t in range(n_periods) if y[i][t]]
                if len(periods) < 2:
                    continue
                # Elegimos cualquier setup salvo el primero: puede fusionarse con uno anterior.
                for t in periods[1:]:
                    candidates.append((i, t))

            if not candidates:
                # Fallback mínimo para garantizar una solución distinta cuando strength >= 1.
                # Mantenemos la idea lo más cerca posible: retiramos un setup tardío si existe,
                # o encendemos el primer período de un ítem con setups escasos si no hay más.
                any_on = [(i, t) for i in range(n_items) for t in range(n_periods) if y[i][t]]
                if not any_on:
                    break
                i, t = rng.choice(any_on)
                if t > 0:
                    y[i][t] = False
                else:
                    # Si el único setup está en t0, movemos la "consolidación" al siguiente período
                    # para forzar distinta solución; el LP decidirá el inventario.
                    if n_periods > 1:
                        y[i][1] = True
                continue

            i, t = rng.choice(candidates)
            y[i][t] = False

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    strength = params.get("strength", 1)
    return BackwardLotShift(problem, strength=strength)
