from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "congestion_aware_period_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "swap_radius": {"type": "int", "range": [1, 3]},
        "period_pressure_weight": {"type": "float", "range": [0.0, 5.0]},
    },
}


class CongestionAwarePeriodSwap:
    def __init__(self, swap_radius: int = 1, period_pressure_weight: float = 1.0):
        self.swap_radius = max(1, int(swap_radius))
        self.period_pressure_weight = float(period_pressure_weight)

    def perturb(self, sol, strength: float, rng: Random):
        n_items = len(sol)
        n_periods = len(sol[0]) if n_items else 0
        if n_items == 0 or n_periods == 0:
            return sol

        s = [list(row) for row in sol]

        period_load = [sum(1 for i in range(n_items) if s[i][t]) for t in range(n_periods)]
        t_cong = max(range(n_periods), key=lambda t: period_load[t] + self.period_pressure_weight * t / max(1, n_periods - 1))

        k = max(1, int(round(strength)))
        for _ in range(k):
            donors = [i for i in range(n_items) if s[i][t_cong]]
            receivers = [i for i in range(n_items) if not s[i][t_cong]]
            if donors and receivers:
                i_out = rng.choice(donors)
                i_in = rng.choice(receivers)

                # Mueve un setup del ítem saturado a un período cercano del otro ítem.
                s[i_out][t_cong] = False
                candidates = [t for t in range(max(0, t_cong - self.swap_radius), min(n_periods, t_cong + self.swap_radius + 1))]
                rng.shuffle(candidates)
                placed = False
                for t in candidates:
                    if t != t_cong and not s[i_in][t]:
                        s[i_in][t] = True
                        placed = True
                        break
                if not placed:
                    s[i_in][t_cong] = True
                    s[i_out][t_cong] = True
            else:
                # Fallback: toggle en la vecindad de mayor presión.
                i = rng.randrange(n_items)
                t = t_cong
                s[i][t] = not s[i][t]

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    return CongestionAwarePeriodSwap(**params)
