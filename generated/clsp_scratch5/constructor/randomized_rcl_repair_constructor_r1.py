from __future__ import annotations

from random import Random
from typing import Tuple

from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel

COMPONENT = {
    "name": "randomized_rcl_repair_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "alpha": {"type": "float", "range": [0.05, 1.0]},
        "repair_rounds": {"type": "int", "range": [1, 10]},
    },
}


class RandomizedRCLRepairConstructor:
    """Constructor tipo GRASP: construye una solución aleatorizada sobre una lista restringida y luego repara."""

    def __init__(self, problem: LotSizingModel, alpha: float = 0.3, repair_rounds: int = 4):
        self.problem = problem
        self.alpha = alpha
        self.repair_rounds = repair_rounds

    def _construct(self, inst: CLSPInstance, rng: Random) -> Tuple[Tuple[bool, ...], ...]:
        n, m = inst.n_items, inst.n_periods
        sol = [[False] * m for _ in range(n)]
        # Lista restringida por urgencia: demanda futura, setup time e inventario
        for t in range(m):
            cand = []
            for i in range(n):
                future = sum(inst.demand[i][tt] for tt in range(t, m))
                if future <= 0:
                    continue
                score = future / (1.0 + inst.holding_cost[i]) + 0.25 * inst.setup_cost[i] - 0.5 * inst.setup_time[i]
                cand.append((score, i))
            if not cand:
                continue
            cand.sort(reverse=True)
            rcl_size = max(1, int(len(cand) * self.alpha))
            chosen = rng.choice(cand[:rcl_size])[1]
            sol[chosen][t] = True
            # probabilidad de abrir un segundo setup si hay holgura
            if len(cand) > 1 and rng.random() < self.alpha * 0.5:
                for _, i in cand[:rcl_size]:
                    if i != chosen:
                        sol[i][t] = True
                        break
        return tuple(tuple(r) for r in sol)

    def _repair_once(self, inst: CLSPInstance, sol: Tuple[Tuple[bool, ...], ...], rng: Random) -> Tuple[Tuple[bool, ...], ...]:
        if self.problem.is_feasible(sol):
            return sol
        n, m = inst.n_items, inst.n_periods
        cur = [list(r) for r in sol]
        # Inserta setups en posiciones con mayor holgura y mayor demanda acumulada.
        ranking = []
        for t in range(m):
            slack = inst.capacity[t] - sum(inst.setup_time[i] for i in range(n) if cur[i][t])
            for i in range(n):
                if cur[i][t] or slack < inst.setup_time[i]:
                    continue
                future = sum(inst.demand[i][tt] for tt in range(t, m))
                if future <= 0:
                    continue
                ranking.append((future / (1.0 + inst.holding_cost[i]) + slack, i, t))
        ranking.sort(reverse=True)
        for _, i, t in ranking:
            cur[i][t] = True
            trial = tuple(tuple(r) for r in cur)
            if self.problem.is_feasible(trial):
                return trial
        return tuple(tuple(r) for r in cur)

    def build(self, inst: CLSPInstance, rng: Random):
        best = None
        # Varias construcciones aleatorizadas, todas deterministas dada la semilla de rng.
        for _ in range(self.repair_rounds):
            cand = self._construct(inst, rng)
            for _k in range(3):
                if self.problem.is_feasible(cand):
                    break
                cand = self._repair_once(inst, cand, rng)
            if self.problem.is_feasible(cand):
                best = cand
                break
            if best is None:
                best = cand
        if best is not None and self.problem.is_feasible(best):
            return best

        # Fallback final: densifica por períodos hasta factibilidad.
        cur = [list(r) for r in (best if best is not None else self._construct(inst, rng))]
        for t in range(inst.n_periods):
            for i in range(inst.n_items):
                if not cur[i][t]:
                    cur[i][t] = True
                    trial = tuple(tuple(r) for r in cur)
                    if self.problem.is_feasible(trial):
                        return trial
        return tuple(tuple(r) for r in cur)


def build_component(problem, alpha: float = 0.3, repair_rounds: int = 4):
    return RandomizedRCLRepairConstructor(problem, alpha=alpha, repair_rounds=repair_rounds)
