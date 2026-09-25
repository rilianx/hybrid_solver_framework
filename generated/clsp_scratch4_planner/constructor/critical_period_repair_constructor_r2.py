from random import Random
from typing import Tuple


COMPONENT = {
    "name": "critical_period_repair_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "max_repairs": {"type": "int", "range": [1, 50]},
        "lookback": {"type": "int", "range": [1, 20]},
    },
}


class CriticalPeriodRepairConstructor:
    """Constructor por reparación de períodos críticos.

    Idea:
    1) Arranca con una solución muy simple: setups en todos los períodos con demanda.
    2) Si falta cobertura para alguna demanda, añade setups en períodos anteriores
       con holgura suficiente.
    3) Prioriza ítems con alto coste de setup y bajo coste de inventario.
    """

    def __init__(self, max_repairs: int = 20, lookback: int = 8):
        self.max_repairs = max_repairs
        self.lookback = lookback

    @staticmethod
    def _copy_sol(sol):
        return tuple(tuple(row) for row in sol)

    def _initial_solution(self, inst) -> Tuple[Tuple[bool, ...], ...]:
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False] * n_periods for _ in range(n_items)]
        for i in range(n_items):
            has_demand = False
            for t in range(n_periods):
                if inst.demand[i][t] > 0:
                    sol[i][t] = True
                    has_demand = True
            if not has_demand:
                sol[i][0] = True
        return tuple(tuple(row) for row in sol)

    def _period_usage(self, inst, sol):
        used = []
        for t in range(inst.n_periods):
            st = sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])
            used.append(st)
        return used

    def _priority(self, inst, i: int) -> float:
        return float(inst.setup_cost[i]) / (float(inst.holding_cost[i]) + 1e-9)

    def _candidate_periods(self, inst, t_crit: int):
        start = max(0, t_crit - self.lookback)
        return list(range(start, t_crit + 1))

    def _repair_once(self, inst, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        if hasattr(inst, "capacity"):
            cap = inst.capacity
        else:
            cap = [0.0] * n_periods

        used = self._period_usage(inst, sol)
        periods = sorted(range(n_periods), key=lambda t: (cap[t] - used[t], -t))
        # Primero intentamos reparar períodos con menos holgura, porque suelen ser los críticos.
        for t_crit in periods:
            slack = cap[t_crit] - used[t_crit]
            # Si el período ya está sobrado, no hace falta tocarlo.
            if slack > 1e-9:
                continue

            candidates = [i for i in range(n_items) if sol[i][t_crit]]
            if not candidates:
                candidates = list(range(n_items))
            candidates.sort(key=lambda i: (-self._priority(inst, i), rng.random()))

            best = None
            for i in candidates:
                for u in self._candidate_periods(inst, t_crit):
                    if u == t_crit:
                        continue
                    if sol[i][u]:
                        continue
                    # Solo añadimos si el período anterior tiene holgura suficiente.
                    if cap[u] - used[u] >= inst.setup_time[i] - 1e-9:
                        score = (
                            cap[u] - used[u],
                            self._priority(inst, i),
                            -u,
                        )
                        if best is None or score > best[0]:
                            best = (score, i, u)

            if best is not None:
                _, i, u = best
                new_sol = [list(row) for row in sol]
                new_sol[i][u] = True
                return tuple(tuple(row) for row in new_sol), True

        # Si no encontramos períodos críticos por capacidad, intentamos reforzar
        # la cobertura temporal de ítems con demanda tardía.
        for i in range(n_items):
            demanded_periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]
            if not demanded_periods:
                continue
            first_d = demanded_periods[0]
            last_d = demanded_periods[-1]
            # Si solo hay un setup antes del último período demandado, buscamos uno extra
            # en un período anterior con más holgura.
            setups_before_last = [t for t in range(0, last_d + 1) if sol[i][t]]
            if len(setups_before_last) <= 1:
                candidates_u = list(range(max(0, last_d - self.lookback), last_d + 1))
                candidates_u.sort(key=lambda u: (cap[u] - used[u], -u), reverse=True)
                for u in candidates_u:
                    if sol[i][u]:
                        continue
                    if cap[u] - used[u] >= inst.setup_time[i] - 1e-9:
                        new_sol = [list(row) for row in sol]
                        new_sol[i][u] = True
                        return tuple(tuple(row) for row in new_sol), True

        return sol, False

    def build(self, inst, rng: Random):
        sol = self._initial_solution(inst)

        # Reparación iterativa sobre períodos críticos.
        for _ in range(self.max_repairs):
            if hasattr(inst, "capacity") and hasattr(inst, "n_periods"):
                pass
            sol, changed = self._repair_once(inst, sol, rng)
            if not changed:
                break

        return sol


def build_component(problem, max_repairs: int = 20, lookback: int = 8):
    constructor = CriticalPeriodRepairConstructor(max_repairs=max_repairs, lookback=lookback)

    class _WrappedConstructor(CriticalPeriodRepairConstructor):
        def build(self, inst, rng: Random):
            sol = super().build(inst, rng)
            if problem.is_feasible(sol):
                return sol

            n_items, n_periods = inst.n_items, inst.n_periods

            for _ in range(self.max_repairs * 2):
                if problem.is_feasible(sol):
                    return sol

                used = self._period_usage(inst, sol)
                cap = inst.capacity
                # Elegimos el período más saturado o, si no hay saturación, el más tardío
                # donde pueda faltar cobertura temporal.
                critical_periods = [t for t in range(n_periods) if cap[t] - used[t] <= 1e-9]
                if critical_periods:
                    t_crit = min(critical_periods, key=lambda t: (cap[t] - used[t], -t))
                else:
                    t_crit = max(range(n_periods), key=lambda t: t)

                candidates = [i for i in range(n_items) if sol[i][t_crit]]
                if not candidates:
                    candidates = list(range(n_items))
                candidates.sort(key=lambda i: (-self._priority(inst, i), rng.random()))

                repaired = False
                for i in candidates:
                    for u in range(max(0, t_crit - self.lookback), t_crit + 1):
                        if u == t_crit:
                            continue
                        if sol[i][u]:
                            continue
                        if cap[u] - used[u] >= inst.setup_time[i] - 1e-9:
                            new_sol = [list(row) for row in sol]
                            new_sol[i][u] = True
                            candidate = tuple(tuple(row) for row in new_sol)
                            if problem.is_feasible(candidate):
                                return candidate
                            sol = candidate
                            repaired = True
                            break
                    if repaired:
                        break

                if not repaired:
                    # Añadimos un setup en el período anterior con más holgura para
                    # reforzar cobertura temporal.
                    best = None
                    for i in candidates:
                        for u in range(max(0, t_crit - self.lookback), t_crit + 1):
                            if u == t_crit or sol[i][u]:
                                continue
                            slack = cap[u] - used[u]
                            if slack >= inst.setup_time[i] - 1e-9:
                                score = (slack, self._priority(inst, i), -u)
                                if best is None or score > best[0]:
                                    best = (score, i, u)
                    if best is None:
                        break
                    _, i, u = best
                    new_sol = [list(row) for row in sol]
                    new_sol[i][u] = True
                    sol = tuple(tuple(row) for row in new_sol)

            return sol

    return _WrappedConstructor(max_repairs=max_repairs, lookback=lookback)
