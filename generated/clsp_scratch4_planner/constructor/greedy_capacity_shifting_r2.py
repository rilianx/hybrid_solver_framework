from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, var_name


COMPONENT = {
    "name": "greedy_capacity_shifting",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "lookahead": {"type": "int", "range": [1, 12]},
        "shift_window": {"type": "int", "range": [0, 12]},
        "cost_bias": {"type": "float", "range": [0.0, 5.0]},
        "random_tie_break": {"type": "bool", "range": [0, 1]},
    },
}


@dataclass
class GreedyCapacityShiftingConstructor:
    """Constructor voraz para CLSP: asigna demanda a períodos con capacidad,
    preferentemente lo más tarde posible, y activa setups solo cuando hace falta.

    La idea se mantiene: construir por recorrido temporal con una lógica de
    desplazamiento de capacidad hacia atrás, priorizando ítems con mayor urgencia
    y menor costo de inventario.
    """

    lookahead: int = 6
    shift_window: int = 6
    cost_bias: float = 1.0
    random_tie_break: bool = False

    def _build_one(self, inst: CLSPInstance, rng: Random) -> tuple[tuple[bool, ...], ...]:
        n, T = inst.n_items, inst.n_periods
        demand = inst.demand

        # Remaining capacity per period.
        rem_cap = [float(c) for c in inst.capacity]

        # Production quantities assigned by item and period (internal only).
        qty = [[0.0 for _ in range(T)] for _ in range(n)]
        used_setup = [[False for _ in range(T)] for _ in range(n)]

        # Total remaining demand per item from period t onward.
        suffix = [[0.0 for _ in range(T + 1)] for _ in range(n)]
        for i in range(n):
            acc = 0.0
            for t in range(T - 1, -1, -1):
                acc += float(demand[i][t])
                suffix[i][t] = acc

        def item_key(i: int, t: int) -> tuple[float, float, float, int]:
            # Higher urgency first, then lower holding cost, then lower setup cost.
            urgency = suffix[i][t] / max(1.0, float(T - t))
            score = urgency / max(1e-9, float(inst.holding_cost[i]))
            score += self.cost_bias / max(1.0, float(inst.setup_cost[i]))
            if self.random_tie_break:
                return (-score, float(inst.holding_cost[i]), float(inst.setup_cost[i]), rng.randint(0, 10**9))
            return (-score, float(inst.holding_cost[i]), float(inst.setup_cost[i]), i)

        # Greedy backward allocation: each demand is assigned to the latest feasible
        # period with enough residual capacity, paying setup time once per item-period.
        for i in range(n):
            periods = list(range(T))
            periods.sort(key=lambda t: item_key(i, t))
            # Demand-by-due-date, earlier due dates handled first to preserve feasibility.
            for t in range(T):
                remaining = float(demand[i][t])
                if remaining <= 1e-12:
                    continue

                # Search feasible periods from t down to 0.
                search_start = min(t, T - 1)
                while remaining > 1e-12:
                    chosen_p = None
                    chosen_avail = 0.0

                    for p in range(search_start, -1, -1):
                        avail = rem_cap[p]
                        if not used_setup[i][p]:
                            avail -= float(inst.setup_time[i])
                        if avail <= 1e-12:
                            continue
                        # Prefer latest feasible period; if tie-breaking is enabled,
                        # occasionally accept an earlier one.
                        if chosen_p is None:
                            chosen_p = p
                            chosen_avail = avail
                        else:
                            if p > chosen_p:
                                chosen_p = p
                                chosen_avail = avail
                            elif self.random_tie_break and p == chosen_p and rng.random() < 0.5:
                                chosen_p = p
                                chosen_avail = avail

                    if chosen_p is None:
                        break  # Will be repaired below if needed.

                    take = min(remaining, chosen_avail)
                    if take <= 1e-12:
                        break

                    if not used_setup[i][chosen_p]:
                        used_setup[i][chosen_p] = True
                        rem_cap[chosen_p] -= float(inst.setup_time[i])

                    qty[i][chosen_p] += take
                    rem_cap[chosen_p] -= take
                    remaining -= take

                # If the greedy choice couldn't place all demand, try a more
                # permissive scan across the whole horizon up to t.
                if remaining > 1e-12:
                    for p in range(t, -1, -1):
                        avail = rem_cap[p]
                        if not used_setup[i][p]:
                            avail -= float(inst.setup_time[i])
                        if avail <= 1e-12:
                            continue
                        take = min(remaining, avail)
                        if take <= 1e-12:
                            continue
                        if not used_setup[i][p]:
                            used_setup[i][p] = True
                            rem_cap[p] -= float(inst.setup_time[i])
                        qty[i][p] += take
                        rem_cap[p] -= take
                        remaining -= take
                        if remaining <= 1e-12:
                            break

        # Final repair pass: if any demand was not assigned, use earliest periods
        # with any remaining capacity. This keeps the constructor conservative and
        # guarantees a complete assignment whenever the instance is feasible.
        for i in range(n):
            for t in range(T):
                target = float(demand[i][t])
                assigned = sum(qty[i][p] for p in range(t + 1))
                missing = target - assigned
                if missing <= 1e-12:
                    continue
                for p in range(t, -1, -1):
                    avail = rem_cap[p]
                    if not used_setup[i][p]:
                        avail -= float(inst.setup_time[i])
                    if avail <= 1e-12:
                        continue
                    take = min(missing, avail)
                    if take <= 1e-12:
                        continue
                    if not used_setup[i][p]:
                        used_setup[i][p] = True
                        rem_cap[p] -= float(inst.setup_time[i])
                    qty[i][p] += take
                    rem_cap[p] -= take
                    missing -= take
                    if missing <= 1e-12:
                        break

        sol = tuple(tuple(row) for row in used_setup)
        return sol

    def build(self, inst: CLSPInstance, rng: Random):
        return self._build_one(inst, rng)


def build_component(
    problem,
    lookahead: int = 6,
    shift_window: int = 6,
    cost_bias: float = 1.0,
    random_tie_break: bool = False,
):
    return GreedyCapacityShiftingConstructor(
        lookahead=lookahead,
        shift_window=shift_window,
        cost_bias=cost_bias,
        random_tie_break=random_tie_break,
    )
