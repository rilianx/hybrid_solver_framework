from __future__ import annotations

from random import Random
from typing import List, Sequence, Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "itemwise_economic_lots_then_capacity_packing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


def _zeros_matrix(n_items: int, n_periods: int) -> List[List[bool]]:
    return [[False for _ in range(n_periods)] for _ in range(n_items)]


def _to_solution(mat: Sequence[Sequence[bool]]) -> Tuple[Tuple[bool, ...], ...]:
    return tuple(tuple(row) for row in mat)


def _uncapacitated_ww_pattern(inst: CLSPInstance, i: int) -> List[bool]:
    """Wagner-Whitin exact DP for a single item, ignoring shared capacity."""
    d = inst.demand[i]
    T = inst.n_periods
    s = inst.setup_cost[i]
    h = inst.holding_cost[i]

    def lot_cost(k: int, t: int) -> float:
        hold = 0.0
        for u in range(k + 1, t + 1):
            hold += d[u] * h * (u - k)
        return s + hold

    dp = [0.0] + [float("inf")] * T
    pred = [-1] * (T + 1)

    for t in range(1, T + 1):
        best = float("inf")
        best_k = 0
        for k in range(1, t + 1):
            val = dp[k - 1] + lot_cost(k - 1, t - 1)
            if val < best:
                best = val
                best_k = k - 1
        dp[t] = best
        pred[t] = best_k

    y = [False] * T
    t = T
    while t > 0:
        k = pred[t]
        y[k] = True
        t = k
    if any(v > 1e-12 for v in d) and not any(y):
        y[0] = True
    return y


def _all_demand_periods_pattern(inst: CLSPInstance) -> List[List[bool]]:
    """Safe fallback: setup in every period where the item has demand."""
    n, T = inst.n_items, inst.n_periods
    sol = _zeros_matrix(n, T)
    for i in range(n):
        for t in range(T):
            if inst.demand[i][t] > 1e-12:
                sol[i][t] = True
        if any(inst.demand[i][t] > 1e-12 for t in range(T)) and not any(sol[i]):
            sol[i][0] = True
    return sol


class ItemwiseEconomicLotsThenCapacityPacking:
    """Construye lotes económicos por ítem y luego los empaqueta respetando capacidad compartida."""

    def __init__(self):
        pass

    def build(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods

        # 1) Itemwise economic setup patterns.
        sol = _zeros_matrix(n, T)
        for i in range(n):
            row = _uncapacitated_ww_pattern(inst, i)
            sol[i] = row

        # Guarantee that every demand-bearing item has at least one setup.
        for i in range(n):
            if any(inst.demand[i][t] > 1e-12 for t in range(T)) and not any(sol[i]):
                sol[i][0] = True

        tup = _to_solution(sol)
        model = LotSizingModel(inst)
        if model.is_feasible(tup):
            return tup

        # 2) Conservative, contract-safe fallback: setup on every demand period.
        # This preserves the item's demand coverage and usually restores feasibility by
        # giving the LP more freedom to allocate production across the horizon.
        dense = _all_demand_periods_pattern(inst)
        tup_dense = _to_solution(dense)
        if model.is_feasible(tup_dense):
            return tup_dense

        # 3) Final fallback: if needed, fully activate all periods for demand-bearing items.
        # This is deliberately conservative to ensure a feasible constructor output.
        full = _zeros_matrix(n, T)
        for i in range(n):
            if any(inst.demand[i][t] > 1e-12 for t in range(T)):
                for t in range(T):
                    full[i][t] = True
        tup_full = _to_solution(full)
        if model.is_feasible(tup_full):
            return tup_full

        # In the very unlikely case that the instance itself is infeasible, return the
        # most expressive pattern available.
        return tup_full


def build_component(problem, **params):
    return ItemwiseEconomicLotsThenCapacityPacking()
