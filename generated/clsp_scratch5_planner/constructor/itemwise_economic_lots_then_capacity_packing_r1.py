from __future__ import annotations

from dataclasses import dataclass
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


def _pattern_load(inst: CLSPInstance, sol: Sequence[Sequence[bool]]) -> List[float]:
    load = [0.0 for _ in range(inst.n_periods)]
    for t in range(inst.n_periods):
        prod = 0.0
        st = 0.0
        for i in range(inst.n_items):
            if sol[i][t]:
                prod += inst.demand[i][t]
                st += inst.setup_time[i]
        load[t] = prod + st
    return load


def _uncapacitated_ww_pattern(inst: CLSPInstance, i: int) -> List[bool]:
    """Wagner-Whitin exact DP for a single item, ignoring shared capacity."""
    d = inst.demand[i]
    T = inst.n_periods
    s = inst.setup_cost[i]
    h = inst.holding_cost[i]

    # prefix demand and prefix holding-weighted demand
    pref_d = [0.0] * (T + 1)
    for t in range(T):
        pref_d[t + 1] = pref_d[t] + d[t]

    # cost of producing all demand from period k to t in k
    def lot_cost(k: int, t: int) -> float:
        # setup + holding to carry demands k..t after production in k
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
    # if there is demand and no setup due to all-zero row, set first period
    if any(v > 1e-12 for v in d) and not any(y):
        y[0] = True
    return y


def _dense_backup_pattern(inst: CLSPInstance) -> List[List[bool]]:
    """Fallback dense-but-still-capacity-aware pattern: one setup per item on a spread grid."""
    n, T = inst.n_items, inst.n_periods
    sol = _zeros_matrix(n, T)
    for i in range(n):
        # Spread setups across the horizon according to item index.
        # Ensures every item has at least one early setup and later opportunities.
        first = (i * max(1, T - 1)) // max(1, n)
        sol[i][first] = True
        # Add another setup if the item has demand in later periods and horizon is long.
        if T >= 4:
            second = min(T - 1, first + max(1, T // 2))
            sol[i][second] = True
    return sol


class ItemwiseEconomicLotsThenCapacityPacking:
    """Construye lotes económicos por ítem y luego los empaqueta respetando capacidad compartida."""

    def __init__(self):
        pass

    def _repair_capacity(self, inst: CLSPInstance, sol: List[List[bool]]) -> List[List[bool]]:
        n, T = inst.n_items, inst.n_periods

        def load_at(t: int) -> float:
            return sum(inst.demand[i][t] for i in range(n) if sol[i][t]) + sum(
                inst.setup_time[i] for i in range(n) if sol[i][t]
            )

        load = _pattern_load(inst, sol)

        # Greedy backward packing: move setups from overloaded periods to earlier slack periods.
        # Candidate move: shift setup of item i from t to t-1 if that preserves a setup before all demand
        # up to t and reduces load in t.
        for _ in range(8 * T * max(1, n)):
            changed = False
            for t in range(T - 1, 0, -1):
                while load[t] > inst.capacity[t] + 1e-9:
                    best = None
                    best_gain = None
                    for i in range(n):
                        if not sol[i][t]:
                            continue
                        # Don't remove the last setup for an item.
                        if sum(1 for tt in range(T) if sol[i][tt]) <= 1:
                            continue
                        if sol[i][t - 1]:
                            continue
                        # Moving this setup earlier shifts the lot demand at t to t-1 in our proxy load.
                        delta_t = inst.demand[i][t] + inst.setup_time[i]
                        delta_prev = inst.demand[i][t - 1] + inst.setup_time[i]
                        # Favor moves that reduce the overloaded period a lot and don't overload earlier period.
                        if load[t - 1] + delta_prev > inst.capacity[t - 1] + 1e-9:
                            continue
                        gain = delta_t - delta_prev
                        if best is None or gain > best_gain:
                            best = i
                            best_gain = gain
                    if best is None:
                        break
                    i = best
                    sol[i][t] = False
                    sol[i][t - 1] = True
                    load[t] -= inst.demand[i][t] + inst.setup_time[i]
                    load[t - 1] += inst.demand[i][t - 1] + inst.setup_time[i]
                    changed = True
                # end while
            if not changed:
                break

        # If still infeasible under the proxy load, add early setups for items with large late demand
        # and shift them backward into the earliest feasible slack periods.
        if any(load[t] > inst.capacity[t] + 1e-9 for t in range(T)):
            for i in range(n):
                if any(sol[i]):
                    continue
                # place one setup at the earliest period with enough room for the local demand proxy
                best_t = None
                for t in range(T):
                    local = inst.demand[i][t] + inst.setup_time[i]
                    if load[t] + local <= inst.capacity[t] + 1e-9:
                        best_t = t
                        break
                if best_t is None:
                    best_t = min(range(T), key=lambda tt: load[tt] - inst.capacity[tt])
                sol[i][best_t] = True
                load[best_t] += inst.demand[i][best_t] + inst.setup_time[i]

        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        n, T = inst.n_items, inst.n_periods

        # 1) Itemwise economic setup patterns.
        sol = _zeros_matrix(n, T)
        for i in range(n):
            row = _uncapacitated_ww_pattern(inst, i)
            sol[i] = row

        # Ensure every demand-bearing item has at least one setup.
        for i in range(n):
            if any(inst.demand[i][t] > 1e-12 for t in range(T)) and not any(sol[i]):
                sol[i][0] = True

        # 2) Capacity packing via backward shifting.
        sol = self._repair_capacity(inst, sol)

        # 3) Deterministic feasibility repair loop: if still infeasible, fall back to denser patterns
        # and repack. The fallback is deterministic and does not use extra randomness.
        model = LotSizingModel(inst)
        tup = _to_solution(sol)
        if not model.is_feasible(tup):
            dense = _dense_backup_pattern(inst)
            dense = self._repair_capacity(inst, dense)
            tup_dense = _to_solution(dense)
            if model.is_feasible(tup_dense):
                return tup_dense

            # Final conservative fallback: keep all current setups and add one early setup to every item.
            # This usually increases the LP's flexibility enough to restore feasibility.
            final = _zeros_matrix(n, T)
            for i in range(n):
                for t in range(T):
                    final[i][t] = sol[i][t] or dense[i][t]
                if not any(final[i]):
                    final[i][0] = True
            final = self._repair_capacity(inst, final)
            tup_final = _to_solution(final)
            if model.is_feasible(tup_final):
                return tup_final

        return tup


def build_component(problem, **params):
    return ItemwiseEconomicLotsThenCapacityPacking()
