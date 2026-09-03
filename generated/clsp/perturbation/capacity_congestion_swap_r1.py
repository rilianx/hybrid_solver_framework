from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import LotSizingModel


COMPONENT = {
    "name": "capacity_congestion_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 15.0]},
        "focus_on_busy_periods": {"type": "bool", "range": [0, 1]},
    },
}


class CapacityCongestionSwap:
    def __init__(self, problem, focus_on_busy_periods: bool = True):
        self.problem = problem
        self.inst = problem.inst
        self.focus_on_busy_periods = focus_on_busy_periods

    def _period_load(self, sol, t: int) -> int:
        return sum(1 for i in range(self.inst.n_items) if sol[i][t])

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        out = [list(row) for row in sol]
        n_moves = max(1, int(round(strength)))

        for _ in range(n_moves):
            loads = [self._period_load(sol, t) for t in range(n_periods)]
            if self.focus_on_busy_periods:
                t_from = max(range(n_periods), key=lambda t: (loads[t], rng.random()))
            else:
                t_from = rng.randrange(n_periods)

            # Busca un ítem con setup en t_from
            items = [i for i in range(n_items) if out[i][t_from]]
            if not items:
                # Si el período elegido está vacío, fuerza un cambio mínimo
                i = rng.randrange(n_items)
                t_to = rng.randrange(n_periods)
                if t_to == t_from and n_periods > 1:
                    t_to = (t_to + 1) % n_periods
                out[i][t_to] = not out[i][t_to]
                continue

            i = rng.choice(items)

            # Mover a un período menos congestionado, o intercambiar con otro ítem
            candidate_periods = list(range(n_periods))
            candidate_periods.sort(key=lambda t: (loads[t], rng.random()))
            t_to = candidate_periods[0]
            if t_to == t_from and n_periods > 1:
                t_to = candidate_periods[1]

            if not out[i][t_to]:
                out[i][t_from] = False
                out[i][t_to] = True
            else:
                # Swap estructural: intercambia con otro ítem en el destino
                j_candidates = [j for j in range(n_items) if j != i and out[j][t_to]]
                if j_candidates:
                    j = rng.choice(j_candidates)
                    out[i][t_from] = False
                    out[i][t_to] = True
                    out[j][t_to] = False
                    out[j][t_from] = True
                else:
                    # Si no hay swap posible, desplaza a otro período
                    alt = [t for t in range(n_periods) if t != t_from and not out[i][t]]
                    if alt:
                        t_new = rng.choice(alt)
                        out[i][t_from] = False
                        out[i][t_new] = True

        new_sol = tuple(tuple(row) for row in out)
        if new_sol == sol:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            out[i][t] = not out[i][t]
            new_sol = tuple(tuple(row) for row in out)
        return new_sol


def build_component(problem, **params):
    focus_on_busy_periods = bool(params.get("focus_on_busy_periods", True))
    return CapacityCongestionSwap(problem, focus_on_busy_periods=focus_on_busy_periods)
