from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "backward_inventory_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "inventory_bias": {"type": "float", "range": [0.0, 2.0]},
        "repair_rounds": {"type": "int", "range": [1, 30]},
    },
}


class BackwardInventoryConstructor:
    """Construcción hacia atrás: coloca setups lo más tarde posible y usa inventario para cubrir demanda previa."""

    def __init__(self, problem: LotSizingModel, inventory_bias: float = 1.0, repair_rounds: int = 10):
        self.problem = problem
        self.inventory_bias = inventory_bias
        self.repair_rounds = repair_rounds

    def _empty_sol(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int, value: bool):
        return tuple(
            tuple(value if (ii == i and tt == t) else sol[ii][tt] for tt in range(len(sol[0])))
            for ii in range(len(sol))
        )

    def _late_cover_plan(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods
        sol = self._empty_sol(inst)

        # Items with high holding cost are penalized for early production, so we postpone them.
        item_order = list(range(n))
        item_order.sort(key=lambda i: (inst.holding_cost[i], inst.setup_time[i], -sum(inst.demand[i]), rng.random()))

        for i in item_order:
            # Last setup is always placed at the last positive-demand period.
            pos = [t for t in range(T) if inst.demand[i][t] > 0]
            if not pos:
                continue
            last = pos[-1]
            sol = self._set(sol, i, last, True)

            # Additional earlier setups if demand is very spread out or setup time is large.
            gaps = []
            prev = last
            for t in range(last - 1, -1, -1):
                if inst.demand[i][t] > 0 and prev - t > 1:
                    gaps.append(t)
                    prev = t
            if gaps:
                for t in gaps:
                    if rng.random() < 0.65:
                        sol = self._set(sol, i, t, True)

            # If the item has early demand and only one setup, hedge by opening the first positive period too.
            if len(pos) >= 2 and rng.random() < 0.5:
                sol = self._set(sol, i, pos[0], True)

        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        sol = self._late_cover_plan(inst, rng)
        if self.problem.is_feasible(sol):
            return sol

        # Repair: move some setups earlier and enrich the pattern around capacity-tight periods.
        n, T = inst.n_items, inst.n_periods
        for _ in range(self.repair_rounds):
            if self.problem.is_feasible(sol):
                return sol
            # Try inserting an earlier setup for items that already have a late setup.
            candidates = []
            for i in range(n):
                setup_periods = [t for t in range(T) if sol[i][t]]
                if not setup_periods:
                    continue
                earliest = min(setup_periods)
                for t in range(earliest):
                    if not sol[i][t]:
                        candidates.append((inst.holding_cost[i], -inst.setup_time[i], -sum(inst.demand[i][t:]), i, t))
            if not candidates:
                break
            candidates.sort(reverse=True)
            _, _, _, i, t = candidates[0]
            sol = self._set(sol, i, t, True)

        if self.problem.is_feasible(sol):
            return sol

        # Final fallback: make every item active on its positive-demand periods.
        for i in range(n):
            for t in range(T):
                if inst.demand[i][t] > 0:
                    sol = self._set(sol, i, t, True)
        return sol


def build_component(problem, inventory_bias: float = 1.0, repair_rounds: int = 10):
    return BackwardInventoryConstructor(problem, inventory_bias=inventory_bias, repair_rounds=repair_rounds)
