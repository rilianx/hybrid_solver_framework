from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "critical_period_seeding",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "priority_mode": {"type": "cat", "values": ["criticality", "holding", "demand"]},
        "use_rng_shuffle": {"type": "bool", "range": [0, 1]},
    },
}


class CriticalPeriodSeedingConstructor:
    """Constructor por siembra en períodos críticos y retroceso de lotes.

    La idea es identificar primero los períodos más tensos y asignarles
    producciones/setup imprescindibles, propagando luego el resto de la demanda
    hacia atrás en la medida de lo posible.
    """

    def __init__(self, problem: Any, priority_mode: str = "criticality", use_rng_shuffle: bool = True):
        self.problem = problem
        self.inst = problem.inst
        self.priority_mode = priority_mode
        self.use_rng_shuffle = use_rng_shuffle

    def _period_pressure(self) -> list[float]:
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        pressure: list[float] = []
        cum_dem = 0.0
        cum_cap = 0.0
        min_setup = min(inst.setup_time) if n_items > 0 else 0.0
        for t in range(n_periods):
            cum_dem += sum(inst.demand[i][t] for i in range(n_items))
            cum_cap += inst.capacity[t]
            pressure.append((cum_dem + min_setup * (t + 1)) / max(cum_cap, 1e-9))
        return pressure

    def _item_key(self, i: int, pressure: list[float]) -> tuple[float, float, float]:
        inst = self.inst
        demand_sum = sum(inst.demand[i])
        weighted = sum((t + 1) * inst.demand[i][t] for t in range(inst.n_periods))
        setup_penalty = inst.setup_time[i] * inst.setup_cost[i]
        if self.priority_mode == "holding":
            return (inst.holding_cost[i], demand_sum, weighted)
        if self.priority_mode == "demand":
            return (demand_sum, weighted, setup_penalty)
        crit_score = sum(inst.demand[i][t] * pressure[t] for t in range(inst.n_periods))
        return (crit_score, setup_penalty, weighted)

    def _construct(self, rng: Random) -> tuple[tuple[bool, ...], ...]:
        inst = self.inst
        n_items, n_periods = inst.n_items, inst.n_periods
        pressure = self._period_pressure()

        order = list(range(n_items))
        order.sort(key=lambda i: self._item_key(i, pressure), reverse=True)
        if self.use_rng_shuffle and n_items > 1:
            block = max(2, n_items // 5)
            for start in range(0, n_items, block):
                chunk = order[start : start + block]
                rng.shuffle(chunk)
                order[start : start + block] = chunk

        rem = [float(inst.capacity[t]) for t in range(n_periods)]
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        for i in order:
            st = float(inst.setup_time[i])
            for t in range(n_periods - 1, -1, -1):
                qty = float(inst.demand[i][t])
                if qty <= 1e-12:
                    continue

                remaining = qty
                p = t
                while remaining > 1e-12 and p >= 0:
                    if not sol[i][p]:
                        if rem[p] + 1e-9 < st:
                            p -= 1
                            continue
                        avail = rem[p] - st
                        if avail <= 1e-12:
                            p -= 1
                            continue
                        take = min(remaining, avail)
                        sol[i][p] = True
                        rem[p] -= st + take
                        remaining -= take
                    else:
                        avail = rem[p]
                        if avail <= 1e-12:
                            p -= 1
                            continue
                        take = min(remaining, avail)
                        rem[p] -= take
                        remaining -= take
                    if remaining > 1e-12:
                        p -= 1

                if remaining > 1e-12:
                    # último recurso: abre el setup en el primer período con mayor holgura previa
                    candidates = [pp for pp in range(t + 1) if rem[pp] + 1e-9 >= st]
                    if not candidates:
                        candidates = list(range(t + 1))
                    pp = max(candidates, key=lambda x: rem[x])
                    if not sol[i][pp]:
                        sol[i][pp] = True
                        rem[pp] = max(0.0, rem[pp] - st)
                    take = min(remaining, rem[pp])
                    rem[pp] -= take
                    remaining -= take

        return tuple(tuple(row) for row in sol)

    def build(self, inst, rng: Random):
        cand = self._construct(rng)
        if self.problem.is_feasible(cand):
            return cand

        # Reparación conservadora: reintenta con el orden inverso.
        order_rng = Random(rng.random())
        self.use_rng_shuffle = False
        cand2 = self._construct(order_rng)
        self.use_rng_shuffle = True
        if self.problem.is_feasible(cand2):
            return cand2

        # Reparación final: asegura al menos un setup para cada ítem con demanda,
        # en el período más tardío posible con capacidad remanente.
        inst = self.inst
        rem = [float(inst.capacity[t]) for t in range(inst.n_periods)]
        sol = [[False for _ in range(inst.n_periods)] for _ in range(inst.n_items)]

        for i in range(inst.n_items):
            if sum(inst.demand[i]) <= 1e-12:
                continue
            st = float(inst.setup_time[i])
            for t in range(inst.n_periods - 1, -1, -1):
                if sum(inst.demand[i][t:]) <= 1e-12:
                    continue
                if rem[t] + 1e-9 >= st:
                    sol[i][t] = True
                    rem[t] -= st
                    break
            else:
                # Si no hay periodo con setup holgado, toma el de mayor capacidad residual.
                t = max(range(inst.n_periods), key=lambda p: rem[p])
                sol[i][t] = True
                rem[t] = max(0.0, rem[t] - st)

        cand3 = tuple(tuple(row) for row in sol)
        if self.problem.is_feasible(cand3):
            return cand3

        return cand3


def build_component(problem, priority_mode: str = "criticality", use_rng_shuffle: bool = True):
    return CriticalPeriodSeedingConstructor(
        problem=problem,
        priority_mode=priority_mode,
        use_rng_shuffle=use_rng_shuffle,
    )
