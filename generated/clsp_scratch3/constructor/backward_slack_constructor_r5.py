from __future__ import annotations

from random import Random

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
    """Constructor hacia atrás: distribuye demanda en períodos previos con setups suficientes."""

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

    def _total_demand(self, inst, i: int) -> float:
        return sum(inst.demand[i][t] for t in range(inst.n_periods))

    def build(self, inst, rng: Random):
        sol = self._empty(inst)
        n_items, n_periods = inst.n_items, inst.n_periods

        # Capacidad residual por período: el LP todavía debe respetar setup_time + producción.
        residual_cap = [float(inst.capacity[t]) for t in range(n_periods)]

        # Orden: ítems más demandantes y más "costosos" primero, para reducir riesgo de infeasibilidad.
        items = list(range(n_items))
        items.sort(
            key=lambda i: (
                -self._total_demand(inst, i),
                -max(inst.setup_time[i] for _ in range(1)),
                i,
            )
        )

        # Para cada ítem, asignamos su demanda total a los períodos más tardíos con capacidad libre.
        # Cada período usado para el ítem necesita un setup; la producción restante consume capacidad.
        for i in items:
            remaining = self._total_demand(inst, i)
            if remaining <= 0:
                continue

            # Recorremos hacia atrás para mantener la idea backward.
            for t in range(n_periods - 1, -1, -1):
                if remaining <= 1e-12:
                    break

                # Si usamos este período por primera vez para el ítem, reservamos el setup_time.
                if residual_cap[t] <= inst.setup_time[i]:
                    continue

                # Cantidad máxima producible aquí si activamos el setup.
                max_here = residual_cap[t] - inst.setup_time[i]
                if max_here <= 0:
                    continue

                q = min(remaining, max_here)
                if q <= 0:
                    continue

                sol = self._set(sol, i, t)
                residual_cap[t] -= q + inst.setup_time[i]
                remaining -= q

            # Reparación conservadora: si todavía queda demanda, habilitamos períodos previos
            # con la mayor capacidad remanente disponible y repartimos la parte faltante.
            if remaining > 1e-12:
                candidates = list(range(n_periods))
                candidates.sort(key=lambda t: (-residual_cap[t], t))
                for t in candidates:
                    if remaining <= 1e-12:
                        break
                    if residual_cap[t] <= inst.setup_time[i]:
                        continue
                    max_here = residual_cap[t] - inst.setup_time[i]
                    if max_here <= 0:
                        continue
                    q = min(remaining, max_here)
                    if q <= 0:
                        continue
                    sol = self._set(sol, i, t)
                    residual_cap[t] -= q + inst.setup_time[i]
                    remaining -= q

            # Último recurso: si un ítem quedó sin ningún setup, activar el primer período con demanda.
            if not any(sol[i]):
                for t in range(n_periods):
                    if inst.demand[i][t] > 0:
                        sol = self._set(sol, i, t)
                        break

        return sol


def build_component(problem, window: int = 4, risk: float = 0.35):
    return BackwardSlackConstructor(window=window, risk=risk)
