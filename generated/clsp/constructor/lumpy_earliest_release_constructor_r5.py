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
    """Constructor conservador: activa setups lo antes posible, respetando la demanda por bloques."""

    def __init__(self, window_bias: float = 0.35):
        self.window_bias = window_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        # Capacidad residual por período, incluyendo el tiempo de setup.
        remaining_cap = [float(inst.capacity[t]) for t in range(n_periods)]

        def first_demand_period(i: int) -> int:
            for t in range(n_periods):
                if inst.demand[i][t] > 0:
                    return t
            return n_periods

        def total_demand(i: int) -> float:
            return float(sum(inst.demand[i][t] for t in range(n_periods)))

        def demand_blocks(i: int):
            blocks = []
            t = 0
            while t < n_periods:
                while t < n_periods and inst.demand[i][t] <= 0:
                    t += 1
                if t >= n_periods:
                    break
                start = t
                while t < n_periods and inst.demand[i][t] > 0:
                    t += 1
                blocks.append(start)
            return blocks

        items = list(range(n_items))
        items.sort(key=lambda i: (first_demand_period(i), -total_demand(i)))

        if n_items >= 2 and self.window_bias > 0.0 and rng.random() < self.window_bias:
            i = rng.randrange(n_items)
            j = rng.randrange(n_items)
            if i != j:
                items[i], items[j] = items[j], items[i]
                items.sort(key=lambda i: (first_demand_period(i), -total_demand(i)))

        for i in items:
            dem = [float(inst.demand[i][t]) for t in range(n_periods)]
            if sum(dem) <= 0.0:
                continue

            s_time = float(inst.setup_time[i])

            # Un setup al inicio de cada bloque de demanda es suficiente para permitir
            # producir y almacenar la demanda del bloque y de los períodos posteriores.
            # Si el período del bloque está congestionado, buscamos la posición más temprana
            # disponible no posterior al comienzo del bloque.
            for bstart in demand_blocks(i):
                if any(sol[i][t] for t in range(0, bstart + 1)):
                    # Ya existe un setup para cubrir este bloque.
                    continue

                placed = False

                # Preferimos el período más temprano posible para "earliest release",
                # pero nunca después del comienzo del bloque.
                for t in range(0, bstart + 1):
                    if remaining_cap[t] >= s_time:
                        sol[i][t] = True
                        remaining_cap[t] -= s_time
                        placed = True
                        break

                if not placed:
                    # Último recurso: si ningún período tiene capacidad residual suficiente,
                    # intentamos colocar el setup en el propio comienzo del bloque para no
                    # desplazar la demanda a un período posterior.
                    # (Las instancias validadas suelen admitir este caso; evitamos además
                    # dejar el bloque sin ninguna activación.)
                    if not sol[i][bstart]:
                        sol[i][bstart] = True

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_bias: float = 0.35):
    return LumpyEarliestReleaseConstructor(window_bias=window_bias)
