from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel, var_name

COMPONENT = {
    "name": "reverse_greedy_all_setups_pruning",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class ReverseGreedyAllSetupsPruning:
    """Construcción por densificación y poda: arranca con todos los setups y elimina los menos útiles si sigue siendo factible."""

    def __init__(self):
        pass

    @staticmethod
    def _all_true(inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def build(self, inst: CLSPInstance, rng: Random):
        model = LotSizingModel(inst)

        sol = self._all_true(inst)
        if not model.is_feasible(sol):
            return sol

        items = list(range(inst.n_items))
        periods = list(range(inst.n_periods))
        # Prioridad de poda: setups caros y con poco "beneficio" de inventario.
        candidates: List[Tuple[float, int, int]] = []
        for i in items:
            for t in periods:
                score = (
                    inst.setup_cost[i]
                    + 0.1 * inst.setup_time[i]
                    - 0.05 * inst.holding_cost[i] * (inst.n_periods - t)
                )
                candidates.append((score, i, t))
        rng.shuffle(candidates)
        candidates.sort(key=lambda x: x[0], reverse=True)

        current = sol
        for _, i, t in candidates:
            if not current[i][t]:
                continue
            trial = tuple(
                tuple(
                    (current[ii][tt] if (ii, tt) != (i, t) else False)
                    for tt in range(inst.n_periods)
                )
                for ii in range(inst.n_items)
            )
            if model.is_feasible(trial):
                current = trial

        return current if model.is_feasible(current) else sol


def build_component(problem, **params):
    return ReverseGreedyAllSetupsPruning()
