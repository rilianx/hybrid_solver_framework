from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "single_setup_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "max_shift": {"type": "int", "range": [1, 4]},
    },
}


class SingleSetupShift:
    def __init__(self, max_shift: int = 2):
        self.max_shift = max(1, int(max_shift))

    def perturb(self, sol, strength: float, rng: Random):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        if n_items == 0 or n_periods == 0:
            return sol

        s = [list(row) for row in sol]
        k = max(1, int(round(strength)))
        shift_cap = max(1, min(self.max_shift, n_periods - 1 if n_periods > 1 else 1))

        for _ in range(k):
            items = list(range(n_items))
            rng.shuffle(items)
            moved = False
            for i in items:
                active = [t for t in range(n_periods) if s[i][t]]
                if not active:
                    continue
                t = rng.choice(active)
                direction = -1 if (n_periods == 1 or rng.random() < 0.5) else 1
                for dist in range(1, shift_cap + 1):
                    nt = t + direction * dist
                    if 0 <= nt < n_periods and nt != t:
                        s[i][t] = False
                        s[i][nt] = True
                        moved = True
                        break
                if moved:
                    break

            if not moved:
                i = rng.randrange(n_items)
                t = rng.randrange(n_periods)
                s[i][t] = not s[i][t]

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    return SingleSetupShift(**params)
