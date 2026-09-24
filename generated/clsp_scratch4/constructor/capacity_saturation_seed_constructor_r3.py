from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "capacity_saturation_seed_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class CapacitySaturationSeedConstructor:
    """Constructor conservador: activa, por defecto, un setup por ítem en una fecha de demanda positiva
    y solo añade setups adicionales si hace falta para recuperar factibilidad.
    """

    def __init__(self):
        pass

    @staticmethod
    def _first_positive_demand_period(inst: CLSPInstance, i: int) -> int:
        for t, d in enumerate(inst.demand[i]):
            if d > 0:
                return t
        return 0

    @staticmethod
    def _periods_with_positive_demand(inst: CLSPInstance, i: int) -> list[int]:
        return [t for t, d in enumerate(inst.demand[i]) if d > 0]

    def _seed_solution(self, inst: CLSPInstance, rng: Random) -> Tuple[Tuple[bool, ...], ...]:
        rows = [[False] * inst.n_periods for _ in range(inst.n_items)]

        item_order = list(range(inst.n_items))
        rng.shuffle(item_order)
        item_order.sort(
            key=lambda i: (
                -sum(inst.demand[i]),
                -inst.setup_time[i],
                inst.setup_cost[i],
            )
        )

        for i in item_order:
            t = self._first_positive_demand_period(inst, i)
            rows[i][t] = True

        return tuple(tuple(r) for r in rows)

    def _repair_to_feasible(
        self, inst: CLSPInstance, model: LotSizingModel, sol: Tuple[Tuple[bool, ...], ...], rng: Random
    ) -> Tuple[Tuple[bool, ...], ...]:
        if model.is_feasible(sol):
            return sol

        rows = [list(r) for r in sol]

        # Añadimos setups solo en períodos donde el ítem ya tiene demanda positiva,
        # priorizando ítems con más demanda total y setups "útiles" más tempranos.
        item_order = list(range(inst.n_items))
        rng.shuffle(item_order)
        item_order.sort(key=lambda i: (-sum(inst.demand[i]), inst.setup_cost[i], -inst.setup_time[i]))

        for i in item_order:
            candidate_periods = self._periods_with_positive_demand(inst, i)
            if not candidate_periods:
                candidate_periods = [0]

            # Probar primero el primer periodo con demanda y luego el resto, sin crear patrones densos.
            for t in candidate_periods:
                if rows[i][t]:
                    continue
                rows[i][t] = True
                trial = tuple(tuple(r) for r in rows)
                if model.is_feasible(trial):
                    return trial

        # Último recurso: abrir setups adicionales de forma muy selectiva, pero solo donde hay demanda.
        for i in item_order:
            for t in self._periods_with_positive_demand(inst, i):
                if rows[i][t]:
                    continue
                rows[i][t] = True
                trial = tuple(tuple(r) for r in rows)
                if model.is_feasible(trial):
                    return trial

        # Si aún así no fuese factible, devolver el último patrón probado.
        return tuple(tuple(r) for r in rows)

    def build(self, inst: CLSPInstance, rng: Random):
        model = LotSizingModel(inst)
        candidate = self._seed_solution(inst, rng)
        return self._repair_to_feasible(inst, model, candidate, rng)


def build_component(problem, **params):
    return CapacitySaturationSeedConstructor()
