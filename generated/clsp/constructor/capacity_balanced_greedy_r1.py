from __future__ import annotations

from random import Random
from typing import List

COMPONENT = {
    "name": "capacity_balanced_greedy",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class CapacityBalancedGreedy:
    """Construye por períodos: prioriza ítems con demanda urgente y coloca setups sólo donde cabe la carga resultante."""

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        y = [[False for _ in range(n_periods)] for _ in range(n_items)]
        remaining = [float(c) for c in inst.capacity]
        used = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Prioridad: demanda acumulada restante e intensidad de setup-cost para favorecer ítems "caros" de setupear.
        order = list(range(n_items))
        order.sort(key=lambda i: (sum(inst.demand[i]), inst.setup_cost[i], -inst.holding_cost[i]), reverse=True)

        for t in range(n_periods):
            # Ítems con demanda en el período t, ordenados por urgencia.
            urgent = [i for i in order if inst.demand[i][t] > 0]
            # También permitimos anticipar ítems con demanda futura si queda espacio.
            future = [i for i in order if i not in urgent]
            candidates = urgent + future

            # Repetimos mientras haya capacidad para nuevos setups o producción.
            progress = True
            while progress:
                progress = False
                for i in candidates:
                    # Si este ítem ya tiene setup en t, sólo intentamos aprovechar capacidad con producción futura/presente.
                    if not used[i][t]:
                        need_here = sum(inst.demand[i][k] for k in range(t, n_periods))
                        if need_here <= 0:
                            continue
                        setup = float(inst.setup_time[i])
                        if remaining[t] < setup + 1e-12:
                            continue
                        # Activamos el setup en t sólo si podemos asignar carga suficiente; usamos un umbral conservador.
                        if need_here + setup * 0.5 <= remaining[t] + 1e-12:
                            used[i][t] = True
                            y[i][t] = True
                            remaining[t] -= setup
                            progress = True
                    # Intentamos meter algo de producción implícita reduciendo capacidad del período.
                    if used[i][t]:
                        future_need = sum(inst.demand[i][k] for k in range(t, n_periods))
                        if future_need <= 1e-12:
                            continue
                        qty = min(future_need, remaining[t])
                        if qty > 1e-12:
                            remaining[t] -= qty
                            progress = True

            # Si quedan demandas futuras y todavía capacidad en t, abrimos setups adicionales guiados por costo de inventario.
            if remaining[t] > 1e-12:
                extras = [i for i in order if not used[i][t] and sum(inst.demand[i][k] for k in range(t, n_periods)) > 0]
                extras.sort(key=lambda i: (inst.holding_cost[i], inst.setup_time[i], -inst.setup_cost[i]))
                for i in extras:
                    if remaining[t] < float(inst.setup_time[i]) + 1e-12:
                        continue
                    y[i][t] = True
                    used[i][t] = True
                    remaining[t] -= float(inst.setup_time[i])
                    if remaining[t] <= 1e-12:
                        break

        # Seguridad: si algún ítem quedó sin setup pero con demanda, asignarlo al último período con capacidad.
        for i in range(n_items):
            if any(y[i]) or sum(inst.demand[i]) <= 0:
                continue
            for t in range(n_periods - 1, -1, -1):
                if remaining[t] >= float(inst.setup_time[i]) - 1e-12:
                    y[i][t] = True
                    remaining[t] -= float(inst.setup_time[i])
                    break

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    return CapacityBalancedGreedy()
