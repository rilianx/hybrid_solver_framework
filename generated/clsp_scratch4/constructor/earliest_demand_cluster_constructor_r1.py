from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "earliest_demand_cluster_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class EarliestDemandClusterConstructor:
    """Agrupa demanda por ítem en el tiempo: pone un setup en el primer período con demanda y, si hace falta, añade refuerzos en picos futuros."""

    def __init__(self):
        pass

    @staticmethod
    def _all_true(inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _initial_solution(self, inst: CLSPInstance, rng: Random) -> Tuple[Tuple[bool, ...], ...]:
        rows = []
        for i in range(inst.n_items):
            demand = inst.demand[i]
            first = next((t for t, d in enumerate(demand) if d > 0), 0)
            row = [False] * inst.n_periods
            row[first] = True

            # Refuerzos: si hay varios picos separados, abre nuevos setups en los inicios de bloques demandantes.
            t = first + 1
            while t < inst.n_periods:
                if demand[t] > 0 and rng.random() < 0.35:
                    row[t] = True
                t += 1
            rows.append(tuple(row))
        return tuple(rows)

    def build(self, inst: CLSPInstance, rng: Random):
        model = LotSizingModel(inst)
        candidate = self._initial_solution(inst, rng)

        if model.is_feasible(candidate):
            return candidate

        # Reparación conservadora: expandir gradualmente hasta el patrón denso.
        all_true = self._all_true(inst)
        if model.is_feasible(all_true):
            return all_true

        # Si el patrón denso fuese raramente infeasible, devolvemos el mejor intento factible encontrado.
        best = candidate
        best_obj = model.objective(candidate)
        if model.is_feasible(best):
            return best

        # Búsqueda de vecinos por activación de setups en períodos anteriores/futuros.
        current = candidate
        for _ in range(3):
            changed = False
            for i in range(inst.n_items):
                for t in range(inst.n_periods):
                    if current[i][t]:
                        continue
                    trial = tuple(
                        tuple((current[ii][tt] if (ii, tt) != (i, t) else True) for tt in range(inst.n_periods))
                        for ii in range(inst.n_items)
                    )
                    if model.is_feasible(trial):
                        trial_obj = model.objective(trial)
                        if (not model.is_feasible(best)) or trial_obj < best_obj:
                            best, best_obj = trial, trial_obj
                        current = trial
                        changed = True
            if not changed:
                break

        return best if model.is_feasible(best) else all_true


def build_component(problem, **params):
    return EarliestDemandClusterConstructor()
