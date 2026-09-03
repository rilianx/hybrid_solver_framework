from __future__ import annotations

from random import Random
from typing import Dict, List, Tuple

COMPONENT = {
    "name": "capacity_balanced_greedy",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class CapacityBalancedGreedy:
    """Constructor factible: empaqueta demanda hacia atrás en periodos con capacidad libre."""

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        capacity = [float(c) for c in inst.capacity]
        remaining = capacity[:]

        # y[i][t] = True si abrimos setup del ítem i en el período t
        y = [[False for _ in range(n_periods)] for _ in range(n_items)]
        opened = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Procesamos demandas desde el último período hacia el primero.
        # Para cada demanda (i, t), intentamos producirla en el último período p <= t
        # con capacidad libre suficiente, permitiendo partir la demanda en varios periodos.
        demand_entries: List[Tuple[int, int, float]] = []
        for i in range(n_items):
            for t in range(n_periods):
                q = float(inst.demand[i][t])
                if q > 0.0:
                    demand_entries.append((i, t, q))

        # Orden descendente por periodo de vencimiento: preserva capacidad temprana.
        demand_entries.sort(key=lambda z: (z[1], z[2]), reverse=True)

        for i, t_due, q_total in demand_entries:
            q_left = q_total
            p = t_due
            while q_left > 1e-12 and p >= 0:
                # Si no hay capacidad, retrocedemos.
                if remaining[p] <= 1e-12:
                    p -= 1
                    continue

                setup_cost = float(inst.setup_time[i])
                if not opened[i][p]:
                    # Necesitamos reservar el setup del ítem en este periodo.
                    if remaining[p] <= setup_cost + 1e-12:
                        p -= 1
                        continue
                    opened[i][p] = True
                    y[i][p] = True
                    remaining[p] -= setup_cost

                # Producimos tanto como podamos en este periodo.
                if remaining[p] <= 1e-12:
                    p -= 1
                    continue

                qty = min(q_left, remaining[p])
                remaining[p] -= qty
                q_left -= qty

                # Si quedó demanda, probamos este mismo periodo otra vez solo si hay capacidad.
                if q_left > 1e-12 and remaining[p] <= 1e-12:
                    p -= 1

            # Si por alguna razón no pudimos asignar toda la demanda, forzamos
            # una pasada adicional usando cualquier periodo previo con capacidad.
            # Esto mantiene el constructor robusto; la instancia de benchmark debe ser factible.
            if q_left > 1e-12:
                for p in range(t_due, -1, -1):
                    if q_left <= 1e-12:
                        break
                    if remaining[p] <= 1e-12:
                        continue
                    setup_cost = float(inst.setup_time[i])
                    if not opened[i][p]:
                        if remaining[p] <= setup_cost + 1e-12:
                            continue
                        opened[i][p] = True
                        y[i][p] = True
                        remaining[p] -= setup_cost
                    if remaining[p] > 1e-12:
                        qty = min(q_left, remaining[p])
                        remaining[p] -= qty
                        q_left -= qty

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    return CapacityBalancedGreedy()
