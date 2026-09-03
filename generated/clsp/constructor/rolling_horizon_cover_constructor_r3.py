from __future__ import annotations

from random import Random
from typing import List, Tuple


COMPONENT = {
    "name": "rolling_horizon_cover_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class RollingHorizonCoverConstructor:
    """Construcción greedy por horizonte rodante.

    Idea:
    - Procesa los ítems con mayor demanda/coste primero.
    - En cada ítem, intenta ubicar producción en los períodos con más capacidad residual.
    - Cada vez que se usa un período para un ítem, se descuenta también su tiempo de setup.
    """

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods

        # y[i][t] = True si el ítem i se produce en el período t
        y: List[List[bool]] = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Capacidad residual por período
        remaining_cap = [float(c) for c in inst.capacity]

        # Orden de ítems: más demandantes y/o más costosos primero
        item_order = list(range(n_items))
        item_order.sort(
            key=lambda i: (
                float(sum(inst.demand[i])),
                float(inst.setup_cost[i]),
                float(inst.holding_cost[i]),
                float(inst.setup_time[i]),
            ),
            reverse=True,
        )

        eps = 1e-12

        for i in item_order:
            demand_left = float(sum(inst.demand[i]))
            if demand_left <= eps:
                continue

            setup_time_i = float(inst.setup_time[i])

            # Períodos con mayor capacidad primero; desempate aleatorio estable vía rng
            periods = list(range(n_periods))
            periods.sort(key=lambda t: (remaining_cap[t], rng.random()), reverse=True)

            # Intento principal: cubrir toda la demanda de i repartiendo en períodos
            for t in periods:
                if demand_left <= eps:
                    break

                cap_t = remaining_cap[t]
                if cap_t <= eps:
                    continue

                # Necesitamos al menos capacidad para el setup
                if cap_t + eps < setup_time_i:
                    continue

                # Si aún no usamos este período para el ítem, reservamos setup
                if not y[i][t]:
                    y[i][t] = True
                    remaining_cap[t] -= setup_time_i
                    cap_t = remaining_cap[t]

                if cap_t <= eps:
                    continue

                take = min(cap_t, demand_left)
                remaining_cap[t] -= take
                demand_left -= take

            # Reparación final: si queda demanda, volver a intentar con el mejor orden
            if demand_left > eps:
                periods = list(range(n_periods))
                periods.sort(key=lambda t: (remaining_cap[t], rng.random()), reverse=True)
                for t in periods:
                    if demand_left <= eps:
                        break

                    cap_t = remaining_cap[t]
                    if cap_t <= eps or cap_t + eps < setup_time_i:
                        continue

                    if not y[i][t]:
                        y[i][t] = True
                        remaining_cap[t] -= setup_time_i
                        cap_t = remaining_cap[t]

                    if cap_t <= eps:
                        continue

                    take = min(cap_t, demand_left)
                    remaining_cap[t] -= take
                    demand_left -= take

            # Si todavía queda demanda, no hay espacio suficiente en la instancia o el patrón es imposible.
            # No forzamos más cambios para no romper otras asignaciones.

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    return RollingHorizonCoverConstructor()
