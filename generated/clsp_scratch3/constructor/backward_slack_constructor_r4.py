from __future__ import annotations

from math import ceil
from random import Random

from examples.lotsizing.problem_model import var_name

COMPONENT = {
    "name": "backward_slack_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window": {"type": "int", "range": [1, 10]},
        "risk": {"type": "float", "range": [0.0, 1.0]},
    },
}


class BackwardSlackConstructor:
    """Constructor hacia atrás: crea setups suficientes antes de cada demanda y reparte cobertura."""

    def __init__(self, window: int = 4, risk: float = 0.35):
        self.window = window
        self.risk = risk

    def _empty(self, inst):
        return tuple(tuple(False for _ in range(inst.n_periods)) for _ in range(inst.n_items))

    def _set(self, sol, i: int, t: int):
        if sol[i][t]:
            return sol
        row = list(sol[i])
        row[t] = True
        return sol[:i] + (tuple(row),) + sol[i + 1 :]

    def _first_positive_demand(self, inst, i: int):
        for t in range(inst.n_periods):
            if inst.demand[i][t] > 0:
                return t
        return None

    def _last_positive_demand(self, inst, i: int):
        for t in range(inst.n_periods - 1, -1, -1):
            if inst.demand[i][t] > 0:
                return t
        return None

    def _item_has_setup_prefix(self, sol, i: int, t: int) -> bool:
        return any(sol[i][tt] for tt in range(t + 1))

    def build(self, inst, rng: Random):
        sol = self._empty(inst)

        items = list(range(inst.n_items))
        items.sort(
            key=lambda i: (
                self._first_positive_demand(inst, i) is None,
                self._first_positive_demand(inst, i) if self._first_positive_demand(inst, i) is not None else inst.n_periods,
                i,
            )
        )

        # 1) Coloca una base de setups hacia atrás: al menos en el primer período con demanda positiva.
        for i in items:
            first_d = self._first_positive_demand(inst, i)
            if first_d is None:
                continue
            sol = self._set(sol, i, first_d)

        # 2) Refuerzo: si hay demanda en t y todavía no existe setup previo, activa un setup en t.
        #    Esto mantiene la idea backward y evita demandas "antes del primer setup".
        for i in items:
            for t in range(inst.n_periods):
                if inst.demand[i][t] > 0 and not self._item_has_setup_prefix(sol, i, t):
                    sol = self._set(sol, i, t)

        # 3) Reparación de capacidad temporal para items con mucha demanda:
        #    si un item concentra demasiada demanda respecto a un único setup,
        #    añadimos setups anteriores repartidos hacia atrás (sin movimientos compuestos).
        for i in items:
            total_demand = sum(inst.demand[i][t] for t in range(inst.n_periods))
            if total_demand <= 0:
                continue

            first_d = self._first_positive_demand(inst, i)
            last_d = self._last_positive_demand(inst, i)
            if first_d is None or last_d is None:
                continue

            # Cota conservadora de producción por setup: el peor caso es capacidad menos setup_time.
            # Si el item requiere más de esa cantidad, distribuimos en varios períodos.
            max_per_setup = max(1.0, max(inst.capacity[t] - inst.setup_time[i] for t in range(inst.n_periods)))
            needed_setups = max(1, ceil(total_demand / max_per_setup))

            current_setups = [t for t in range(inst.n_periods) if sol[i][t]]
            if len(current_setups) < needed_setups:
                missing = needed_setups - len(current_setups)
                # Distribución hacia atrás entre first_d y last_d, priorizando períodos tempranos.
                candidate_periods = list(range(last_d, -1, -1))
                # preferir períodos dentro de la ventana antes de la demanda final, pero sin excluir otros.
                preferred = [t for t in candidate_periods if t <= last_d]
                chosen = []
                for t in preferred:
                    if not sol[i][t]:
                        chosen.append(t)
                        if len(chosen) == missing:
                            break
                if len(chosen) < missing:
                    for t in candidate_periods:
                        if t not in chosen and not sol[i][t]:
                            chosen.append(t)
                            if len(chosen) == missing:
                                break
                for t in chosen:
                    sol = self._set(sol, i, t)

        # 4) Si un item tiene demanda pero quedó sin setup por alguna esquina rara, activa el primero.
        for i in items:
            if any(inst.demand[i][t] > 0 for t in range(inst.n_periods)) and not any(sol[i]):
                sol = self._set(sol, i, 0)

        return sol


def build_component(problem, window: int = 4, risk: float = 0.35):
    return BackwardSlackConstructor(window=window, risk=risk)
