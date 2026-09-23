from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "item_break_repair",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "focus_fraction": {"type": "float", "range": [0.1, 1.0]},
        "repair_trials": {"type": "int", "range": [1, 12]},
    },
}


class ItemBreakRepairPerturbation:
    def __init__(self, problem, focus_fraction: float = 0.5, repair_trials: int = 4):
        self.problem = problem
        self.inst: CLSPInstance = problem.inst
        self.focus_fraction = max(0.1, min(1.0, float(focus_fraction)))
        self.repair_trials = max(1, int(repair_trials))

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        if n_items == 0 or n_periods == 0:
            return sol

        k_items = max(1, min(n_items, int(round(self.focus_fraction * max(1.0, strength)))))
        items = list(range(n_items))
        rng.shuffle(items)
        chosen = items[:k_items]

        best = None
        best_obj = None

        base = [list(row) for row in sol]
        # Intento 1: romper setups en una ventana corta y dejar que la recolocación
        # genere un plan distinto.
        window = max(1, min(n_periods, int(round(strength))))
        for _ in range(self.repair_trials):
            cand = [row[:] for row in base]
            for i in chosen:
                if n_periods == 1:
                    cand[i][0] = not cand[i][0]
                    continue
                t0 = rng.randrange(n_periods)
                t1 = min(n_periods, t0 + window)
                segment = list(range(t0, t1))
                if not segment:
                    segment = [rng.randrange(n_periods)]
                # Si hay al menos un setup en el segmento, apaga uno; si no, enciende uno.
                on = [t for t in segment if cand[i][t]]
                if on:
                    cand[i][rng.choice(on)] = False
                else:
                    cand[i][rng.choice(segment)] = True

                # Reparación ligera: asegurar que cada ítem tocado tenga al menos un setup.
                if not any(cand[i]):
                    cand[i][rng.randrange(n_periods)] = True

            sol2 = tuple(tuple(row) for row in cand)
            if sol2 == sol:
                i = rng.choice(chosen)
                t = rng.randrange(n_periods)
                cand[i][t] = not cand[i][t]
                sol2 = tuple(tuple(row) for row in cand)

            obj = self.problem.objective(sol2)
            if best is None or obj < best_obj:
                best = sol2
                best_obj = obj

        return best


def build_component(problem, focus_fraction: float = 0.5, repair_trials: int = 4):
    return ItemBreakRepairPerturbation(problem, focus_fraction=focus_fraction, repair_trials=repair_trials)
