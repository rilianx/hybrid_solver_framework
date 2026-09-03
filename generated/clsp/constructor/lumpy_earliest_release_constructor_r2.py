from __future__ import annotations

from random import Random

from examples.lotsizing.problem_model import CLSPInstance


COMPONENT = {
    "name": "lumpy_earliest_release_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "requires": [],
    "params": {
        "window_bias": {"type": "float", "range": [0.0, 1.0]},
    },
}


class LumpyEarliestReleaseConstructor:
    """Constructor conservador: garantiza cobertura temporal produciendo en todos los períodos con demanda."""

    def __init__(self, window_bias: float = 0.35):
        self.window_bias = window_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        for i in range(n_items):
            demand_periods = [t for t in range(n_periods) if inst.demand[i][t] > 0]

            if not demand_periods:
                # Ítem sin demanda: dejamos al menos un setup arbitrario y barato.
                sol[i][0] = True
                continue

            # Regla principal: si hay demanda en un período, habilitamos producción en ese período.
            # Esto evita faltantes por retroceso temporal y mantiene la solución lo más simple posible.
            for t in demand_periods:
                sol[i][t] = True

            # Pequeña variación conservadora: ocasionalmente añadimos un setup temprano adicional
            # para ítems "lumpy", sin eliminar ninguno de los necesarios.
            if len(demand_periods) >= 3 and rng.random() < self.window_bias:
                sol[i][demand_periods[0]] = True

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_bias: float = 0.35):
    return LumpyEarliestReleaseConstructor(window_bias=window_bias)
