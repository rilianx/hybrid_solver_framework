from random import Random
from typing import List, Tuple

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
    2) Si hay infeasibilidad, identifica períodos críticos y desplaza setups hacia
       períodos anteriores con más holgura.
    3) Prioriza ítems con alto coste de setup y baja penalización de inventario
       (holding cost bajo), para que el adelanto de producción sea más conveniente.
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
            for t in range(n_periods):
                if inst.demand[i][t] > 0:
                    sol[i][t] = True
        # Si algún ítem tiene demanda total positiva pero ningún período positivo
        # por redondeos/rareza, lo anclamos al primer período.
        for i in range(n_items):
            if not any(sol[i]):
                sol[i][0] = True
        return tuple(tuple(row) for row in sol)

    def _period_usage(self, inst, sol):
        used = []
        for t in range(inst.n_periods):
            st = sum(inst.setup_time[i] for i in range(inst.n_items) if sol[i][t])
            prod_proxy = sum(inst.demand[i][t] for i in range(inst.n_items) if sol[i][t])
            used.append(st + prod_proxy)
        return used

    def _priority(self, inst, i: int) -> float:
        return float(inst.setup_cost[i]) / (float(inst.holding_cost[i]) + 1e-9)

    def _repair_once(self, inst, sol, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        used = self._period_usage(inst, sol)
        overloads = [(used[t] - inst.capacity[t], t) for t in range(n_periods) if used[t] > inst.capacity[t] + 1e-9]
        if not overloads:
            return sol, False

        overloads.sort(reverse=True)
        _, t_crit = overloads[0]

        # Candidatos: ítems con setup en el período crítico.
        candidates = [i for i in range(n_items) if sol[i][t_crit]]
        if not candidates:
            # Si no hay setups en el período crítico, intentamos activar un setup
            # en un período anterior para algún ítem con demanda cerca.
            candidates = list(range(n_items))

        # Ordena por prioridad alta (setup caro, holding bajo), con desempate aleatorio determinista.
        candidates.sort(key=lambda i: (-self._priority(inst, i), rng.random()))

        # Busca un período anterior con holgura donde mover el setup.
        best_move = None
        for i in candidates:
            for u in range(max(0, t_crit - self.lookback), t_crit):
                if sol[i][u]:
                    continue
                slack_u = inst.capacity[u] - used[u]
                gain_crit = inst.setup_time[i] + (inst.demand[i][t_crit] if inst.demand[i][t_crit] > 0 else 0.0)
                if slack_u + 1e-9 >= inst.setup_time[i]:
                    # Mover el setup libera capacidad en el período crítico; el costo de
                    # inventario se acepta porque el ítem tiene prioridad alta.
                    score = (gain_crit, slack_u, -u, self._priority(inst, i))
                    if best_move is None or score > best_move[0]:
                        best_move = (score, i, u)

        if best_move is None:
            # Reparación alternativa: añadir setup en un período anterior con más holgura
            # sin apagar el actual todavía; luego, si mejora, se intenta apagar.
            for i in candidates:
                for u in range(max(0, t_crit - self.lookback), t_crit):
                    if sol[i][u]:
                        continue
                    if inst.capacity[u] - used[u] >= inst.setup_time[i] + 1e-9:
                        new_sol = [list(row) for row in sol]
                        new_sol[i][u] = True
                        return tuple(tuple(row) for row in new_sol), True
            return sol, False

        _, i, u = best_move
        new_sol = [list(row) for row in sol]
        new_sol[i][u] = True
        new_sol[i][t_crit] = False
        return tuple(tuple(row) for row in new_sol), True

    def build(self, inst, rng: Random):
        sol = self._initial_solution(inst)

        # Reparación iterativa sobre períodos críticos.
        for _ in range(self.max_repairs):
            if hasattr(inst, "n_periods") and hasattr(inst, "n_items"):
                # Reparamos guiándonos por la factibilidad del modelo.
                # Si ya es factible, terminamos.
                from examples.lotsizing.problem_model import LotSizingModel  # local import permitido
                # No tenemos acceso al ProblemModel aquí, así que usamos una
                # comprobación estructural posterior en build_component.
            sol, changed = self._repair_once(inst, sol, rng)
            if not changed:
                break

        return sol


def build_component(problem, max_repairs: int = 20, lookback: int = 8):
    constructor = CriticalPeriodRepairConstructor(max_repairs=max_repairs, lookback=lookback)

    # Envoltorio para asegurar que usamos la factibilidad del modelo disponible.
    class _WrappedConstructor(CriticalPeriodRepairConstructor):
        def build(self, inst, rng: Random):
            sol = super().build(inst, rng)
            if problem.is_feasible(sol):
                return sol

            # Reparación adicional dirigida por la explicación del modelo:
            # intenta reforzar setups en períodos previos con holgura.
            n_items, n_periods = inst.n_items, inst.n_periods
            for _ in range(self.max_repairs * 2):
                if problem.is_feasible(sol):
                    return sol

                used = self._period_usage(inst, sol)
                overloads = [(used[t] - inst.capacity[t], t) for t in range(n_periods) if used[t] > inst.capacity[t] + 1e-9]
                if not overloads:
                    break
                overloads.sort(reverse=True)
                _, t_crit = overloads[0]

                # Repara el período más crítico con ítems de mayor prioridad.
                candidates = [i for i in range(n_items) if sol[i][t_crit]]
                if not candidates:
                    candidates = list(range(n_items))
                candidates.sort(key=lambda i: (-self._priority(inst, i), rng.random()))

                repaired = False
                for i in candidates:
                    for u in range(max(0, t_crit - self.lookback), t_crit):
                        if sol[i][u]:
                            continue
                        # Añadir antes si hay holgura suficiente.
                        if inst.capacity[u] - used[u] >= inst.setup_time[i] + 1e-9:
                            new_sol = [list(row) for row in sol]
                            new_sol[i][u] = True
                            if sol[i][t_crit]:
                                new_sol[i][t_crit] = False
                            candidate = tuple(tuple(row) for row in new_sol)
                            if problem.is_feasible(candidate):
                                return candidate
                            sol = candidate
                            repaired = True
                            break
                    if repaired:
                        break

                if not repaired:
                    # Si no logramos mover, agregamos setups en prefijos con más holgura.
                    best = None
                    for i in candidates:
                        for u in range(max(0, t_crit - self.lookback), t_crit):
                            if sol[i][u]:
                                continue
                            slack = inst.capacity[u] - used[u]
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

            # Último recurso: devolver la mejor candidata encontrada.
            return sol

    return _WrappedConstructor(max_repairs=max_repairs, lookback=lookback)
