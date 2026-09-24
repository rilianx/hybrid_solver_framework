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
    """Constructor simple y conservador: activa un único setup por ítem en su primera demanda positiva."""

    def __init__(self):
        pass

    @staticmethod
    def _all_true(inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    @staticmethod
    def _first_positive_demand_period(inst: CLSPInstance, i: int) -> int:
        for t, d in enumerate(inst.demand[i]):
            if d > 0:
                return t
        return 0

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

    def build(self, inst: CLSPInstance, rng: Random):
        model = LotSizingModel(inst)
        candidate = self._seed_solution(inst, rng)

        if model.is_feasible(candidate):
            return candidate

        # Fallback robusto: patrón denso completo.
        all_true = self._all_true(inst)
        if model.is_feasible(all_true):
            return all_true

        # Último intento: activar todos los setups de los ítems más críticos primero.
        current = candidate
        critical_items = sorted(range(inst.n_items), key=lambda i: (-sum(inst.demand[i]), -inst.setup_time[i]))
        for i in critical_items:
            trial = tuple(
                tuple((True if ii == i else current[ii][tt]) for tt in range(inst.n_periods))
                for ii in range(inst.n_items)
            )
            if model.is_feasible(trial):
                current = trial

        return current if model.is_feasible(current) else all_true


def build_component(problem, **params):
    return CapacitySaturationSeedConstructor()
