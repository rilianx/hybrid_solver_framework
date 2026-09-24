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


def _demand_bearing(inst: CLSPInstance, i: int) -> bool:
    return any(inst.demand[i][t] > 1e-12 for t in range(inst.n_periods))


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

    if _demand_bearing(inst, i) and not any(y):
        y[next(t for t in range(T) if d[t] > 1e-12)] = True
    return y


def _first_demand_period(inst: CLSPInstance, i: int) -> int:
    for t in range(inst.n_periods):
        if inst.demand[i][t] > 1e-12:
            return t
    return 0


def _add_setup_in_largest_gap(inst: CLSPInstance, sol: List[List[bool]], i: int) -> bool:
    """Add one economically plausible setup for item i inside its largest uncovered demand gap."""
    T = inst.n_periods
    demand_periods = [t for t in range(T) if inst.demand[i][t] > 1e-12]
    if not demand_periods:
        return False

    setup_periods = [t for t in range(T) if sol[i][t]]
    if len(setup_periods) >= len(demand_periods):
        return False

    # Consider the uncovered demand periods and pick the one that creates the largest
    # forward coverage by setting up there.
    best_t = None
    best_score = -1.0
    for t in demand_periods:
        if sol[i][t]:
            continue
        # Score: remaining demand from t onward before the next setup.
        future = 0.0
        for u in range(t, T):
            future += inst.demand[i][u]
            if sol[i][u]:
                break
        # Slightly prefer earlier placements to keep inventory modest.
        score = future - 1e-6 * t
        if score > best_score:
            best_score = score
            best_t = t

    if best_t is None:
        return False
    sol[i][best_t] = True
    return True


def _dense_demand_pattern(inst: CLSPInstance) -> List[List[bool]]:
    """Fallback with setups only at demand periods."""
    n, T = inst.n_items, inst.n_periods
    sol = _zeros_matrix(n, T)
    for i in range(n):
        for t in range(T):
            if inst.demand[i][t] > 1e-12:
                sol[i][t] = True
        if _demand_bearing(inst, i) and not any(sol[i]):
            sol[i][_first_demand_period(inst, i)] = True
    return sol


class ItemwiseEconomicLotsThenCapacityPacking:
    """Construye lotes económicos por ítem y luego ajusta la capacidad con reparaciones mínimas."""

    def __init__(self, problem=None):
        self.problem = problem

    def build(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods

        # 1) Economic itemwise pattern.
        sol = _zeros_matrix(n, T)
        for i in range(n):
            sol[i] = _uncapacitated_ww_pattern(inst, i)

        # Ensure demand-bearing items have at least one setup.
        for i in range(n):
            if _demand_bearing(inst, i) and not any(sol[i]):
                sol[i][_first_demand_period(inst, i)] = True

        tup = _to_solution(sol)
        model = LotSizingModel(inst)
        if model.is_feasible(tup):
            return tup

        # 2) Minimal capacity-oriented repair: add setups only when needed, item by item.
        # This preserves the economic structure and avoids over-activating periods.
        repaired = [row[:] for row in sol]
        max_rounds = max(1, n * T)
        for _ in range(max_rounds):
            tup = _to_solution(repaired)
            if model.is_feasible(tup):
                return tup

            changed = False
            item_order = list(range(n))
            rng.shuffle(item_order)
            for i in item_order:
                if not _demand_bearing(inst, i):
                    continue
                if _add_setup_in_largest_gap(inst, repaired, i):
                    changed = True
                    break
            if not changed:
                break

        tup = _to_solution(repaired)
        if model.is_feasible(tup):
            return tup

        # 3) Conservative fallback: setups at all demand periods, which still avoids
        # unnecessary periods with zero demand.
        dense = _dense_demand_pattern(inst)
        tup_dense = _to_solution(dense)
        if model.is_feasible(tup_dense):
            return tup_dense

        # 4) Final fallback: keep the best-effort pattern.
        return tup_dense


def build_component(problem, **params):
    return ItemwiseEconomicLotsThenCapacityPacking(problem=problem)
