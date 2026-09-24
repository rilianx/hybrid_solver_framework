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
    """Constructor secuencial forward-capacity, conservador en setups.

    Idea:
    - recorre los períodos en orden;
    - activa setups solo cuando hace falta cubrir demanda futura con capacidad disponible;
    - prioriza adelantar producción en períodos con holgura suficiente y bajo coste incremental;
    - evita encender setups que no aportan cobertura real de demanda.
    """

    def __init__(self, relaxation: float = 0.0, max_repairs: int = 6):
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
    def _item_demand(inst: CLSPInstance, i: int, t0: int = 0, t1: int | None = None) -> float:
        if t1 is None:
            t1 = inst.n_periods - 1
        return float(sum(inst.demand[i][t] for t in range(t0, t1 + 1)))

    def _first_positive_demand_period(self, inst: CLSPInstance, i: int) -> int | None:
        for t in range(inst.n_periods):
            if inst.demand[i][t] > 0.0:
                return t
        return None

    def _choose_setup_period(
        self,
        inst: CLSPInstance,
        y: list[list[bool]],
        load: list[float],
        i: int,
        start_t: int,
    ) -> int | None:
        best_t: int | None = None
        best_key: tuple[float, int] | None = None

        for t in range(start_t, inst.n_periods):
            if y[i][t]:
                continue
            slack = inst.capacity[t] - load[t]
            if slack + 1e-9 < inst.setup_time[i]:
                continue

            future_dem = self._item_demand(inst, i, t, inst.n_periods - 1)
            if future_dem <= 0.0:
                continue

            # Menor coste incremental por unidad de capacidad ocupada.
            # Si hay empate, preferimos el período más temprano.
            score = (inst.holding_cost[i] * future_dem) / max(inst.setup_time[i], 1e-9)
            key = (score, t)
            if best_key is None or key < best_key:
                best_key = key
                best_t = t

        return best_t

    def _initial_seed(self, inst: CLSPInstance) -> list[list[bool]]:
        y = self._empty_y(inst)
        for i in range(inst.n_items):
            t0 = self._first_positive_demand_period(inst, i)
            if t0 is not None:
                y[i][t0] = True
        return y

    def _repair(self, inst: CLSPInstance, y: list[list[bool]]) -> list[list[bool]]:
        # Reparación conservadora: solo añade setups que cubren demanda futura
        # y solo cuando existe holgura suficiente en el período candidato.
        for _ in range(self.max_repairs):
            sol = self._to_sol(y)
            problem_like = type("P", (), {"inst": inst, "is_feasible": lambda self, sol: False})()
            try:
                if hasattr(problem_like, "is_feasible") and problem_like.is_feasible(sol):  # type: ignore[misc]
                    return y
            except Exception:
                pass

            load = self._period_load(inst, y)
            changed = False

            item_order = sorted(
                range(inst.n_items),
                key=lambda i: (-self._item_demand(inst, i), inst.setup_time[i], i),
            )

            for i in item_order:
                first = self._first_positive_demand_period(inst, i)
                if first is None:
                    continue

                # Busca el primer hueco útil a partir del primer periodo con demanda.
                t = self._choose_setup_period(inst, y, load, i, first)
                if t is not None:
                    y[i][t] = True
                    load[t] += inst.setup_time[i]
                    changed = True
                    break

                # Si no hay hueco desde el primer período, probamos con una
                # variante todavía más conservadora: algún período anterior
                # no sirve, así que solo intentamos el primero con suficiente slack
                # y demanda futura no nula.
                for tt in range(first + 1, inst.n_periods):
                    if y[i][tt]:
                        continue
                    if load[tt] + inst.setup_time[i] <= inst.capacity[tt] + 1e-9:
                        if self._item_demand(inst, i, tt, inst.n_periods - 1) > 0.0:
                            y[i][tt] = True
                            load[tt] += inst.setup_time[i]
                            changed = True
                            break
                if changed:
                    break

            if not changed:
                break

        return y

    def _light_diversify(self, inst: CLSPInstance, rng: Random, y: list[list[bool]]) -> list[list[bool]]:
        # Diversificación muy limitada y siempre conservadora:
        # solo añade setups si existen demanda futura y holgura clara.
        if self.relaxation <= 0.0:
            return y
        if rng.random() > self.relaxation:
            return y

        load = self._period_load(inst, y)
        items = list(range(inst.n_items))
        items.sort(key=lambda i: (-self._item_demand(inst, i), inst.setup_time[i], i))

        for i in items:
            t0 = self._first_positive_demand_period(inst, i)
            if t0 is None:
                continue
            for t in range(t0, inst.n_periods):
                if y[i][t]:
                    continue
                if load[t] + inst.setup_time[i] <= inst.capacity[t] + 1e-9:
                    if self._item_demand(inst, i, t, inst.n_periods - 1) > 0.0:
                        y[i][t] = True
                        load[t] += inst.setup_time[i]
                        break
            break

        return y

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        y = self._initial_seed(inst)
        y = self._repair(inst, y)
        y = self._light_diversify(inst, rng, y)
        y = self._repair(inst, y)
        return self._to_sol(y)


def build_component(problem, relaxation: float = 0.0, max_repairs: int = 6):
    return ForwardCapacityGreedy(relaxation=relaxation, max_repairs=max_repairs)
