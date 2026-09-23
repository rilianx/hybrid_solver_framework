from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance

COMPONENT = {
    "name": "critical_period_block_shift",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 6.0]},
    },
}


class CriticalPeriodBlockShift:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        s = [list(row) for row in sol]

        k = max(1, int(round(strength)))
        window = max(1, min(n_periods, k))

        # Elegir una ventana de períodos y mover setups dentro de ella hacia
        # adelante/atrás para romper patrones L4L y crear inventario.
        if n_periods == 1:
            i = rng.randrange(n_items)
            s[i][0] = not s[i][0]
            return tuple(tuple(row) for row in s)

        start = rng.randrange(0, n_periods - window + 1)
        end = start + window - 1
        direction = -1 if rng.random() < 0.5 else 1

        candidates = []
        for i in range(n_items):
            for t in range(start, end + 1):
                if s[i][t]:
                    nt = t + direction
                    if 0 <= nt < n_periods:
                        candidates.append((i, t, nt))

        if not candidates:
            # Fallback: flip una celda dentro de la ventana
            i = rng.randrange(n_items)
            t = rng.randrange(start, end + 1)
            s[i][t] = not s[i][t]
            return tuple(tuple(row) for row in s)

        # Mover varios setups del bloque para perturbar la estructura.
        num_moves = min(len(candidates), max(1, k))
        chosen = rng.sample(candidates, num_moves)
        for i, t, nt in chosen:
            s[i][t] = False
            s[i][nt] = True

        return tuple(tuple(row) for row in s)


def build_component(problem, **params):
    strength = params.get("strength", 2.0)
    return CriticalPeriodBlockShift(problem)
