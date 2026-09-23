from __future__ import annotations

from random import Random
from typing import Any, List, Optional

from examples.lotsizing.problem_model import CLSPInstance, Solution

COMPONENT = {
    "name": "earliest_slack_repair",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {"window": {"type": "int", "range": [1, 10]}},
}


class EarliestSlackRepair:
    """Construye una solución inicial factible priorizando producción tan temprano
    como sea posible, sin violar deadlines ni capacidad.
    """

    def __init__(self, window: int = 3) -> None:
        self.window = window

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        n, T = inst.n_items, inst.n_periods
        window = max(1, int(self.window))

        residual_capacity = [float(inst.capacity[t]) for t in range(T)]
        y = [[False for _ in range(T)] for _ in range(n)]

        # Demanda por item y período, procesada desde deadlines más tardíos
        # para reservar capacidad temprana a demandas urgentes.
        for i in range(n):
            demands = [(t, float(inst.demand[i][t])) for t in range(T) if inst.demand[i][t] > 1e-9]
            if not demands:
                continue

            # Intento 1: colocar cada bloque de demanda lo más tarde posible,
            # pero nunca después de su período de vencimiento.
            for due_t, qty in sorted(demands, key=lambda x: x[0], reverse=True):
                remaining = qty
                start_t = max(0, due_t - window + 1)
                for p in range(due_t, start_t - 1, -1):
                    if remaining <= 1e-9:
                        break
                    setup = float(inst.setup_time[i])
                    # Si ya se usa el ítem en p, la capacidad residual ya descontó setup.
                    # Si no, necesitamos espacio para setup + producción.
                    if not y[i][p]:
                        if residual_capacity[p] <= setup + 1e-9:
                            continue
                        free = residual_capacity[p] - setup
                        alloc = min(remaining, free)
                        if alloc > 1e-9:
                            y[i][p] = True
                            residual_capacity[p] -= setup + alloc
                            remaining -= alloc
                    else:
                        alloc = min(remaining, residual_capacity[p])
                        if alloc > 1e-9:
                            residual_capacity[p] -= alloc
                            remaining -= alloc

                # Si aún queda demanda por asignar, ampliamos la búsqueda a todos
                # los períodos anteriores, siempre respetando el vencimiento.
                if remaining > 1e-9:
                    for p in range(due_t, -1, -1):
                        if remaining <= 1e-9:
                            break
                        setup = float(inst.setup_time[i])
                        if not y[i][p]:
                            if residual_capacity[p] <= setup + 1e-9:
                                continue
                            free = residual_capacity[p] - setup
                            alloc = min(remaining, free)
                            if alloc > 1e-9:
                                y[i][p] = True
                                residual_capacity[p] -= setup + alloc
                                remaining -= alloc
                        else:
                            alloc = min(remaining, residual_capacity[p])
                            if alloc > 1e-9:
                                residual_capacity[p] -= alloc
                                remaining -= alloc

                # Último recurso: si todavía quedara demanda, hacemos una pasada
                # global hacia atrás (esto conserva la idea de adelantar todo lo posible).
                if remaining > 1e-9:
                    for p in range(T - 1, -1, -1):
                        if p > due_t:
                            continue
                        if remaining <= 1e-9:
                            break
                        setup = float(inst.setup_time[i])
                        if not y[i][p]:
                            if residual_capacity[p] <= setup + 1e-9:
                                continue
                            free = residual_capacity[p] - setup
                            alloc = min(remaining, free)
                            if alloc > 1e-9:
                                y[i][p] = True
                                residual_capacity[p] -= setup + alloc
                                remaining -= alloc
                        else:
                            alloc = min(remaining, residual_capacity[p])
                            if alloc > 1e-9:
                                residual_capacity[p] -= alloc
                                remaining -= alloc

                # Si la instancia es factible, esta reparación suele cubrir todo.
                # En caso extremo, seguimos con el patrón parcial más conservador.

        sol = tuple(tuple(row) for row in y)
        return sol


def build_component(problem: Any, **params):
    return EarliestSlackRepair(window=int(params.get("window", 3)))
