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
            return sol

        s = [list(row) for row in sol]
        interval_len = max(1, min(n_periods, int(round(max(1.0, strength) * self.interval_scale * n_periods / 3))))
        start = rng.randrange(0, n_periods - interval_len + 1)
        end = start + interval_len

        item_order = list(range(n_items))
        rng.shuffle(item_order)

        changed = False
        for i in item_order:
            active = [t for t in range(start, end) if s[i][t]]
            if not active:
                continue

            # Destruye un pequeño bloque y lo reconstruye con un patrón más compacto.
            for t in active:
                s[i][t] = False

            keep = 1 if rng.random() > self.restart_bias else 2
            keep = min(keep, interval_len)
            anchors = sorted(rng.sample(range(start, end), keep))
            for t in anchors:
                s[i][t] = True
            changed = True
            break

        if not changed:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            s[i][t] = not s[i][t]
            if n_periods > 1 and not any(s[i]):
                s[i][t] = True

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    return IntervalRebuildPerturbation(**params)
