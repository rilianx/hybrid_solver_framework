from __future__ import annotations

from random import Random


COMPONENT = {
    "name": "interval_rebuild_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "interval_scale": {"type": "float", "range": [0.1, 0.8]},
        "restart_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class IntervalRebuildPerturbation:
    def __init__(self, interval_scale: float = 0.35, restart_bias: float = 0.3):
        self.interval_scale = float(interval_scale)
        self.restart_bias = float(restart_bias)

    def perturb(self, sol, strength: float, rng: Random):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0

        if n_items == 0 or n_periods == 0:
            return tuple(tuple(row) for row in sol)

        s = [list(row) for row in sol]

        # Tamaño del intervalo a reconstruir, escalado por strength.
        eff_strength = max(0.0, float(strength))
        interval_len = int(round(max(1.0, eff_strength) * self.interval_scale * n_periods))
        interval_len = max(1, min(n_periods, interval_len))

        start = rng.randrange(0, n_periods - interval_len + 1)
        end = start + interval_len

        # Primero intentamos encontrar un ítem con setups en el intervalo y
        # reconstruirlo de forma distinta.
        item_order = list(range(n_items))
        rng.shuffle(item_order)

        for i in item_order:
            active = [t for t in range(start, end) if s[i][t]]
            if not active:
                continue

            # Vacía el bloque y vuelve a activar un subconjunto compacto.
            for t in active:
                s[i][t] = False

            # Garantiza que se hace un cambio respecto al original.
            # Elegimos al menos un ancla; a veces dos si el intervalo lo permite.
            max_anchors = min(interval_len, len(active))
            n_anchors = 1
            if max_anchors >= 2 and rng.random() < self.restart_bias:
                n_anchors = 2

            anchors = rng.sample(range(start, end), n_anchors)
            for t in anchors:
                s[i][t] = True

            return tuple(tuple(row) for row in s)

        # Si no había setups en el intervalo para ningún ítem, hacemos un kick
        # seguro: flip de una variable aleatoria.
        i = rng.randrange(n_items)
        t = rng.randrange(n_periods)
        s[i][t] = not s[i][t]

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    return IntervalRebuildPerturbation(**params)
