from random import Random
from typing import List, Tuple

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "period_balanced_anticipative_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class PeriodBalancedAnticipativeConstructor:
    """Rellena períodos de izquierda a derecha, adelantando producción cuando el pico de carga se aproxima."""

    def __init__(self):
        pass

    def _pattern(self, inst: CLSPInstance):
        n, T = inst.n_items, inst.n_periods
        sol = [[False] * T for _ in range(n)]
        remaining = [float(c) for c in inst.capacity]

        # Urgencia: demanda futura / (setup+holding proxy) para empujar ítems "apretados" antes.
        urgency = []
        for i in range(n):
            total = sum(inst.demand[i])
            proxy = inst.setup_cost[i] + 1.0 + sum((t + 1) * inst.holding_cost[i] * inst.demand[i][t] for t in range(T))
            urgency.append((-(total / proxy if proxy > 0 else total), i))
        order = [i for _, i in sorted(urgency)]

        for t in range(T):
            # Carga base: demandas del período t.
            base = sum(inst.demand[i][t] for i in range(n))
            slack = remaining[t] - base
            if slack < 0:
                # Necesitamos adelantar: activamos setups de ítems con demanda futura.
                candidates = [i for i in order if any(inst.demand[i][k] > 1e-9 for k in range(t, T))]
                for i in candidates:
                    if sol[i][t]:
                        continue
                    cost = inst.setup_time[i] + sum(inst.demand[i][k] for k in range(t, T))
                    if cost <= remaining[t] + 1e-9:
                        sol[i][t] = True
                        remaining[t] -= cost
                        slack += cost
                    if slack >= 0:
                        break
            # Si aún queda holgura, usamos algunos setups "preventivos" para períodos próximos.
            if slack > 0:
                for i in order:
                    if sol[i][t]:
                        continue
                    future = [k for k in range(t + 1, T) if inst.demand[i][k] > 1e-9]
                    if not future:
                        continue
                    pull = sum(inst.demand[i][k] for k in future[: max(1, len(future) // 2)])
                    cost = inst.setup_time[i] + pull
                    if cost <= slack + 1e-9:
                        sol[i][t] = True
                        remaining[t] -= cost
                        slack -= cost
                    if slack <= 1e-9:
                        break

        return tuple(tuple(r) for r in sol)

    def _repair(self, problem, inst: CLSPInstance, sol):
        if problem.is_feasible(sol):
            return sol

        n, T = inst.n_items, inst.n_periods
        current = [list(r) for r in sol]
        # Reparación: añade setups hacia atrás en períodos con más capacidad residual.
        for _ in range(n * T * 3):
            trial = tuple(tuple(r) for r in current)
            if problem.is_feasible(trial):
                return trial

            changed = False
            for i in range(n):
                for t in range(T - 1, -1, -1):
                    if inst.demand[i][t] <= 1e-9:
                        continue
                    for p in range(t, -1, -1):
                        if not current[i][p]:
                            current[i][p] = True
                            changed = True
                            break
                    if changed:
                        break
                if changed:
                    break
            if not changed:
                break

        return tuple(tuple(r) for r in current)

    def build(self, inst: CLSPInstance, rng: Random):
        raise RuntimeError("use build_component")


def build_component(problem, **params):
    class _B(PeriodBalancedAnticipativeConstructor):
        def build(self, inst: CLSPInstance, rng: Random):
            sol = self._pattern(inst)
            return self._repair(problem, inst, sol)

    return _B()
