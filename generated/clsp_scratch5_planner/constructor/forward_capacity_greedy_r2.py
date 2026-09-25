from __future__ import annotations

from random import Random
from typing import Any

from examples.lotsizing.problem_model import CLSPInstance, Solution  # type: ignore


COMPONENT = {
    "name": "forward_capacity_greedy",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "relaxation": {"type": "float", "range": [0.0, 1.0]},
        "max_repairs": {"type": "int", "range": [1, 50]},
    },
}


class ForwardCapacityGreedy:
    """Constructor secuencial forward-capacity con reparación conservadora.

    Idea:
    - arranca activando setups donde hay demanda;
    - si la capacidad acumulada no alcanza para cubrir bloques de demanda,
      adelanta setups a períodos anteriores con holgura;
    - usa reparaciones elementales y mantiene la solución inmutable.
    """

    def __init__(self, relaxation: float = 0.25, max_repairs: int = 12):
        self.relaxation = float(relaxation)
        self.max_repairs = int(max_repairs)

    @staticmethod
    def _empty_y(inst: CLSPInstance) -> list[list[bool]]:
        return [[False for _ in range(inst.n_periods)] for _ in range(inst.n_items)]

    @staticmethod
    def _to_sol(y: list[list[bool]]) -> Solution:
        return tuple(tuple(row) for row in y)

    @staticmethod
    def _period_load(inst: CLSPInstance, y: list[list[bool]]) -> list[float]:
        return [
            sum(inst.setup_time[i] for i in range(inst.n_items) if y[i][t])
            for t in range(inst.n_periods)
        ]

    @staticmethod
    def _total_item_demand(inst: CLSPInstance, i: int) -> float:
        return float(sum(inst.demand[i][t] for t in range(inst.n_periods)))

    def _seed_from_demand(self, inst: CLSPInstance, rng: Random) -> list[list[bool]]:
        y = self._empty_y(inst)
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                if inst.demand[i][t] > 0.0:
                    y[i][t] = True

        # Pequeña diversificación controlada: con probabilidad relax se añaden setups
        # tempranos si hay holgura, para facilitar cobertura acumulada.
        load = self._period_load(inst, y)
        for i in range(inst.n_items):
            if self.relaxation <= 0.0:
                continue
            total_dem = self._total_item_demand(inst, i)
            if total_dem <= 0.0:
                continue
            # Añade, como mucho, un setup adicional por item en un período temprano
            # con suficiente holgura, priorizando períodos anteriores.
            if rng.random() < self.relaxation:
                for t in range(inst.n_periods):
                    if y[i][t]:
                        continue
                    if load[t] + inst.setup_time[i] <= inst.capacity[t] + 1e-9:
                        y[i][t] = True
                        load[t] += inst.setup_time[i]
                        break
        return y

    def _best_earlier_setup_period(
        self,
        inst: CLSPInstance,
        y: list[list[bool]],
        load: list[float],
        i: int,
        t_limit: int,
    ) -> int | None:
        best_t: int | None = None
        best_score = None
        for t in range(t_limit + 1):
            if y[i][t]:
                continue
            slack = inst.capacity[t] - load[t]
            if slack + 1e-9 < inst.setup_time[i]:
                continue
            future_demand = float(sum(inst.demand[i][tt] for tt in range(t, t_limit + 1)))
            if future_demand <= 0.0:
                continue
            # Menor coste incremental por unidad de capacidad ocupada:
            # holding esperado por adelantar producción / setup_time.
            score = (inst.holding_cost[i] * future_demand) / max(inst.setup_time[i], 1e-9)
            # Preferir períodos más tempranos solo si el score empata.
            key = (score, t)
            if best_score is None or key < best_score:
                best_score = key
                best_t = t
        return best_t

    def _repair(self, problem: Any, y: list[list[bool]]) -> list[list[bool]]:
        inst: CLSPInstance = problem.inst

        for _ in range(self.max_repairs):
            sol = self._to_sol(y)
            if problem.is_feasible(sol):
                return y

            load = self._period_load(inst, y)

            # 1) Intento dirigido: para cada item, si su patrón de setups parece
            # insuficiente para sostener su demanda acumulada, añade un setup previo
            # con holgura.
            changed = False
            item_order = sorted(
                range(inst.n_items),
                key=lambda i: (-self._total_item_demand(inst, i), inst.setup_time[i], i),
            )
            for i in item_order:
                total_dem = self._total_item_demand(inst, i)
                if total_dem <= 0.0:
                    continue

                # Heurística simple: si tiene setups tardíos y aún queda demanda
                # acumulada sin cobertura, insertar un setup anterior.
                last_setup = -1
                for t in range(inst.n_periods):
                    if y[i][t]:
                        last_setup = t
                if last_setup <= 0:
                    continue

                # Busca el primer período anterior con holgura y con demanda futura.
                t_prev = self._best_earlier_setup_period(inst, y, load, i, last_setup - 1)
                if t_prev is not None:
                    y[i][t_prev] = True
                    load[t_prev] += inst.setup_time[i]
                    changed = True

            if changed:
                continue

            # 2) Fallback: añade setups adicionales en períodos tempranos con más holgura
            # para los ítems con mayor demanda total.
            slack_periods = sorted(
                range(inst.n_periods),
                key=lambda t: (inst.capacity[t] - load[t], -t),
                reverse=True,
            )
            added = False
            for i in item_order:
                if self._total_item_demand(inst, i) <= 0.0:
                    continue
                for t in slack_periods:
                    if y[i][t]:
                        continue
                    if load[t] + inst.setup_time[i] <= inst.capacity[t] + 1e-9:
                        y[i][t] = True
                        load[t] += inst.setup_time[i]
                        added = True
                        break
                if added:
                    break

            if not added:
                break

        return y

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        y = self._seed_from_demand(inst, rng)
        y = self._repair(type("P", (), {"inst": inst, "is_feasible": lambda self, sol: False})(), y)

        # Último intento con el modelo real.
        sol = self._to_sol(y)
        if not hasattr(inst, "n_items") or not hasattr(inst, "n_periods"):
            return sol

        # Si por la reparación conservadora aún no fuese factible, reforzamos
        # añadiendo setups en períodos anteriores con holgura hasta agotar intentos.
        fake_problem = None
        try:
            from examples.lotsizing.problem_model import ProblemModel  # type: ignore
            fake_problem = ProblemModel(inst)  # type: ignore
        except Exception:
            fake_problem = None

        if fake_problem is not None:
            for _ in range(self.max_repairs):
                sol = self._to_sol(y)
                if fake_problem.is_feasible(sol):
                    return sol

                load = self._period_load(inst, y)
                order_items = sorted(
                    range(inst.n_items),
                    key=lambda i: (-self._total_item_demand(inst, i), inst.setup_time[i], i),
                )
                progressed = False
                for i in order_items:
                    # Probar períodos anteriores primero; si no, cualquier período con holgura.
                    for t in range(inst.n_periods):
                        if y[i][t]:
                            continue
                        if load[t] + inst.setup_time[i] <= inst.capacity[t] + 1e-9:
                            y[i][t] = True
                            load[t] += inst.setup_time[i]
                            progressed = True
                            break
                    if progressed:
                        break
                if not progressed:
                    break

        return self._to_sol(y)


def build_component(problem, relaxation: float = 0.25, max_repairs: int = 12):
    return ForwardCapacityGreedy(relaxation=relaxation, max_repairs=max_repairs)
