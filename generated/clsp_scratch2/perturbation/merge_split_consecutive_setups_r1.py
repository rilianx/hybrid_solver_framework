from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "merge_split_consecutive_setups",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "merge_bias": {"type": "float", "range": [0.0, 1.0]},
        "max_span": {"type": "int", "range": [2, 6]},
    },
}


class MergeSplitConsecutiveSetupsPerturbation:
    def __init__(self, problem, merge_bias: float = 0.7, max_span: int = 3):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.merge_bias = max(0.0, min(1.0, float(merge_bias)))
        self.max_span = max(2, int(max_span))

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        cand = [list(row) for row in sol]
        focus_items = list(range(n_items))
        rng.shuffle(focus_items)
        n_focus = max(1, min(n_items, int(round(max(1.0, strength) / 2.0))))
        focus_items = focus_items[:n_focus]

        changed = False
        span_limit = max(2, min(n_periods, int(round(self.max_span * max(1.0, strength) / 2.0))))

        for i in focus_items:
            on = [t for t in range(n_periods) if cand[i][t]]
            if len(on) < 2:
                continue

            # Buscar pares consecutivos para fusionar o separar.
            pairs = [(t1, t2) for t1, t2 in zip(on, on[1:]) if t2 == t1 + 1]
            if pairs and rng.random() < self.merge_bias:
                t1, t2 = rng.choice(pairs)
                # Fusionar: apagar uno de los dos setups consecutivos.
                if rng.random() < 0.5:
                    cand[i][t1] = False
                else:
                    cand[i][t2] = False
                changed = True
            else:
                # Separar: si hay un bloque largo, encender un período intermedio cercano.
                tmin, tmax = on[0], on[-1]
                if tmax - tmin >= 2:
                    left = max(0, tmin - span_limit + 1)
                    right = min(n_periods - 1, tmax + span_limit - 1)
                    candidates = [t for t in range(left, right + 1) if not cand[i][t]]
                    if candidates:
                        t = rng.choice(candidates)
                        cand[i][t] = True
                        changed = True

        if not changed:
            i = rng.choice(focus_items)
            t = rng.randrange(n_periods)
            cand[i][t] = not cand[i][t]

        sol2 = tuple(tuple(row) for row in cand)
        if sol2 == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            cand[i][t] = not cand[i][t]
            sol2 = tuple(tuple(row) for row in cand)

        return sol2


def build_component(problem, merge_bias: float = 0.7, max_span: int = 3):
    return MergeSplitConsecutiveSetupsPerturbation(problem, merge_bias=merge_bias, max_span=max_span)
