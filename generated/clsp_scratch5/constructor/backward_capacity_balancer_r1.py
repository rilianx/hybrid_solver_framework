from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "backward_capacity_balancer",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "extra_setup_prob": {"type": "float", "range": [0.0, 0.5]},
        "priority_bias": {"type": "float", "range": [0.0, 2.0]},
    },
}


class BackwardCapacityBalancer:
    """Construcción por balanceo hacia atrás: asigna setups a períodos tardíos y repara hacia atrás."""

    def __init__(self, problem: LotSizingModel, extra_setup_prob: float = 0.15, priority_bias: float = 0.8):
        self.problem = problem
        self.extra_setup_prob = extra_setup_prob
        self.priority_bias = priority_bias

    def _base_solution(self, inst: CLSPInstance) -> Tuple[Tuple[bool, ...], ...]:
        n, m = inst.n_items, inst.n_periods
        demand_suffix = [sum(inst.demand[i][t] for t in range(m)) for i in range(n)]
        # Orden de prioridad: mayor demanda futura / setup time, con sesgo hacia ítems baratos de almacenar
        order = sorted(
            range(n),
            key=lambda i: (
                -(demand_suffix[i] / max(1.0, inst.setup_time[i]) + self.priority_bias / max(1.0, inst.holding_cost[i])),
                -inst.setup_cost[i],
                i,
            ),
        )
        sol = [[False] * m for _ in range(n)]
        remaining_cap = [float(c) for c in inst.capacity]

        for t in range(m - 1, -1, -1):
            # Ítems con demanda futura aún no cubierto por ningún setup hasta t
            eligible = [i for i in order if sum(inst.demand[i][tt] for tt in range(t + 1, m)) > 0]
            for i in eligible:
                if remaining_cap[t] >= inst.setup_time[i] and (
                    inst.demand[i][t] > 0 or (t > 0 and rng_coin(self.extra_setup_prob, i, t))
                ):
                    sol[i][t] = True
                    remaining_cap[t] -= inst.setup_time[i]
        return tuple(tuple(row) for row in sol)

    def _repair(self, inst: CLSPInstance, sol: Tuple[Tuple[bool, ...], ...], rng: Random) -> Tuple[Tuple[bool, ...], ...]:
        n, m = inst.n_items, inst.n_periods
        cur = [list(row) for row in sol]
        if self.problem.is_feasible(sol):
            return sol

        # Reparación: agrega setups en períodos con holgura, priorizando demandas no cubiertas por prefijo
        for _ in range(n * m * 3):
            if self.problem.is_feasible(tuple(tuple(r) for r in cur)):
                break
            best = None
            best_score = -1e18
            for i in range(n):
                for t in range(m):
                    if cur[i][t]:
                        continue
                    # Score: cubrir demanda futura y usar holgura temprana
                    future = sum(inst.demand[i][tt] for tt in range(t, m))
                    if future <= 0:
                        continue
                    slack = inst.capacity[t] - sum(inst.setup_time[k] for k in range(n) if cur[k][t])
                    if slack < inst.setup_time[i]:
                        continue
                    score = future / (1.0 + inst.holding_cost[i]) + 0.01 * (m - t)
                    if score > best_score:
                        best_score = score
                        best = (i, t)
            if best is None:
                # Desescalar: añade en el período con más holgura aunque no sea ideal
                candidates = []
                for t in range(m):
                    slack = inst.capacity[t] - sum(inst.setup_time[k] for k in range(n) if cur[k][t])
                    for i in range(n):
                        if not cur[i][t] and slack >= inst.setup_time[i]:
                            candidates.append((slack, i, t))
                if not candidates:
                    break
                candidates.sort(reverse=True)
                _, i, t = candidates[0]
                cur[i][t] = True
            else:
                i, t = best
                cur[i][t] = True

        sol2 = tuple(tuple(r) for r in cur)
        if self.problem.is_feasible(sol2):
            return sol2

        # Reparación final: activar setups por etapas hasta factibilidad
        for t in range(m):
            for i in range(n):
                if not cur[i][t]:
                    cur[i][t] = True
                    sol2 = tuple(tuple(r) for r in cur)
                    if self.problem.is_feasible(sol2):
                        return sol2
        return tuple(tuple(r) for r in cur)

    def build(self, inst: CLSPInstance, rng: Random):
        base = self._base_solution(inst)
        sol = self._repair(inst, base, rng)
        if not self.problem.is_feasible(sol):
            # último recurso determinista: densificar por período hasta factibilidad
            cur = [list(r) for r in sol]
            for t in range(inst.n_periods):
                for i in range(inst.n_items):
                    cur[i][t] = True
                    trial = tuple(tuple(r) for r in cur)
                    if self.problem.is_feasible(trial):
                        return trial
            return tuple(tuple(r) for r in cur)
        return sol


def rng_coin(p: float, i: int, t: int) -> bool:
    # auxiliar determinista no aleatorio; depende solo de índices
    if p <= 0.0:
        return False
    if p >= 0.5:
        return True
    return ((i * 1315423911 + t * 2654435761) & 1023) < int(p * 1024)


def build_component(problem, extra_setup_prob: float = 0.15, priority_bias: float = 0.8):
    return BackwardCapacityBalancer(problem, extra_setup_prob=extra_setup_prob, priority_bias=priority_bias)
