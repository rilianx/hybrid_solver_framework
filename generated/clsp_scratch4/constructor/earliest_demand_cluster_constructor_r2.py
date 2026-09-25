from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "earliest_demand_cluster_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class EarliestDemandClusterConstructor:
    """Construye una solución inicial con el primer setup en cada ítem al inicio de su demanda."""

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
            rows.append(tuple(row))
        return tuple(rows)

    def build(self, inst: CLSPInstance, rng: Random):
        model = LotSizingModel(inst)
        candidate = self._initial_solution(inst, rng)

        if model.is_feasible(candidate):
            return candidate

        # Reparación muy conservadora: si hace falta, habilitar todos los períodos.
        # Se usa solo como último recurso para garantizar factibilidad.
        all_true = self._all_true(inst)
        if model.is_feasible(all_true):
            return all_true

        # Si algo fuera excepcionalmente extraño, devolver el mejor intento factible encontrado.
        # Aquí el único candidato factible seguro es all_true; si no lo es, mantenemos candidate.
        return all_true if model.is_feasible(all_true) else candidate


def build_component(problem, **params):
    return EarliestDemandClusterConstructor()
