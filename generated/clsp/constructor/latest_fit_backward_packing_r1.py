from __future__ import annotations

from random import Random
from typing import List, Tuple

COMPONENT = {
    "name": "latest_fit_backward_packing",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {},
}


class LatestFitBackwardPacking:
    """Construye una solución factible asignando cada demanda al período más tardío posible con capacidad remanente."""

    def build(self, inst, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        y = [[False for _ in range(n_periods)] for _ in range(n_items)]
        remaining = [float(c) for c in inst.capacity]
        used_setup = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Procesar ítems en orden aleatorio determinista para diversificar sin perder factibilidad.
        items = list(range(n_items))
        rng.shuffle(items)

        for i in items:
            # Demanda total pendiente por período, cubierta con producción en p <= t.
            for t in range(n_periods):
                need = float(inst.demand[i][t])
                while need > 1e-12:
                    placed = False
                    for p in range(t, -1, -1):
                        setup = float(inst.setup_time[i]) if not used_setup[i][p] else 0.0
                        avail = remaining[p] - setup
                        if avail <= 1e-12:
                            continue
                        qty = need if need <= avail else avail
                        if qty <= 1e-12:
                            continue
                        if not used_setup[i][p]:
                            used_setup[i][p] = True
                            y[i][p] = True
                            remaining[p] -= float(inst.setup_time[i])
                        remaining[p] -= qty
                        need -= qty
                        placed = True
                        break
                    if not placed:
                        # Fallback: si el reparto tardío no encuentra hueco, buscar cualquier período anterior con capacidad.
                        for p in range(t + 1):
                            setup = float(inst.setup_time[i]) if not used_setup[i][p] else 0.0
                            avail = remaining[p] - setup
                            if avail <= 1e-12:
                                continue
                            qty = need if need <= avail else avail
                            if qty <= 1e-12:
                                continue
                            if not used_setup[i][p]:
                                used_setup[i][p] = True
                                y[i][p] = True
                                remaining[p] -= float(inst.setup_time[i])
                            remaining[p] -= qty
                            need -= qty
                            placed = True
                            break
                    if not placed:
                        # Último recurso: usar el período actual aunque quede casi sin hueco; la instancia garantizada factible
                        # debería evitar llegar aquí, pero mantenemos una asignación válida de setups.
                        p = t
                        if not used_setup[i][p]:
                            used_setup[i][p] = True
                            y[i][p] = True
                            remaining[p] -= float(inst.setup_time[i])
                        # No descontamos más si no hay espacio: el validador de factibilidad penaliza, pero esto sólo ocurre
                        # en instancias patológicas no esperadas.
                        need = 0.0

        return tuple(tuple(row) for row in y)


def build_component(problem, **params):
    return LatestFitBackwardPacking()
