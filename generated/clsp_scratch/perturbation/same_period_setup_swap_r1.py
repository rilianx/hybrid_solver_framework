from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "same_period_setup_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 8.0]},
    },
}


class SamePeriodSetupSwap:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        s = [list(row) for row in sol]

        k = max(1, int(round(strength)))
        swaps = max(1, k)

        # Elegimos períodos congestionados o al azar y hacemos swaps entre ítems
        # para mantener el número de setups por período pero cambiar la asignación.
        period_candidates = list(range(n_periods))
        rng.shuffle(period_candidates)

        made = 0
        for t in period_candidates:
            on = [i for i in range(n_items) if s[i][t]]
            off = [i for i in range(n_items) if not s[i][t]]
            if not on or not off:
                continue

            i_on = rng.choice(on)
            i_off = rng.choice(off)

            # Swap en el mismo período: preserva cardinalidad del período pero cambia
            # qué ítems se producen, útil para aliviar setups caros o redistribuir carga.
            s[i_on][t] = False
            s[i_off][t] = True
            made += 1
            if made >= swaps:
                return tuple(tuple(row) for row in s)

        # Fallback: intercambio entre dos celdas distintas si no hubo swaps posibles.
        cells = [(i, t) for i in range(n_items) for t in range(n_periods)]
        if len(cells) >= 2:
            (i1, t1), (i2, t2) = rng.sample(cells, 2)
            s[i1][t1], s[i2][t2] = s[i2][t2], s[i1][t1]
        else:
            s[0][0] = not s[0][0]

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return SamePeriodSetupSwap(problem)
