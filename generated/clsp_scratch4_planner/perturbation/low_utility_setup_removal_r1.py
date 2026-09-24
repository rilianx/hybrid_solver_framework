from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "low_utility_setup_removal",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 12.0]}
    },
}


class LowUtilitySetupRemoval:
    def __init__(self, problem: Any, strength: float = 3.0):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.default_strength = strength

    def _setup_utility(self, sol, i: int, t: int) -> float:
        """Menor es peor: setups caros con poco volumen cubierto son candidatos a apagarse."""
        inst = self.inst
        if not sol[i][t]:
            return float("inf")

        n_periods = inst.n_periods
        # Demanda cubierta por este setup hasta el siguiente setup del mismo ítem.
        next_t = n_periods
        for tt in range(t + 1, n_periods):
            if sol[i][tt]:
                next_t = tt
                break

        covered = 0.0
        for tt in range(t, next_t):
            covered += inst.demand[i][tt]

        # Si solo produce muy poco antes del siguiente setup, utilidad baja.
        # Penaliza setups caros respecto al volumen que cubren.
        setup_cost = inst.setup_cost[i]
        holding = inst.holding_cost[i]
        span = max(1, next_t - t)
        utility = (covered + 1.0) / (setup_cost + 1.0)
        utility += 0.05 * (1.0 / span)
        utility -= 0.001 * holding
        return utility

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods

        # Asegura al menos un cambio para strength >= 1.
        s = max(1.0, float(strength))
        target = max(1, min(n_items * n_periods, int(round(s))))

        candidates = []
        for i in range(n_items):
            for t in range(n_periods):
                if sol[i][t]:
                    candidates.append((self._setup_utility(sol, i, t), i, t))

        # Ordena por menor utilidad y añade algo de aleatoriedad en empates.
        rng.shuffle(candidates)
        candidates.sort(key=lambda x: x[0])

        chosen = set()
        for _, i, t in candidates:
            if len(chosen) >= target:
                break
            chosen.add((i, t))

        if not chosen:
            # Fallback: apaga cualquier setup y, si fuese necesario, enciende otro.
            for i in range(n_items):
                for t in range(n_periods):
                    if sol[i][t]:
                        chosen.add((i, t))
                        break
                if chosen:
                    break

        new_sol = []
        changed = False
        for i in range(n_items):
            row = []
            for t in range(n_periods):
                val = sol[i][t]
                if (i, t) in chosen:
                    val = not val
                    changed = True
                row.append(val)
            new_sol.append(tuple(row))

        # Garantiza solución distinta.
        if not changed:
            i = rng.randrange(n_items)
            t = rng.randrange(n_periods)
            row = list(new_sol[i])
            row[t] = not row[t]
            new_sol[i] = tuple(row)

        return tuple(new_sol)


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return LowUtilitySetupRemoval(problem, strength=strength)
