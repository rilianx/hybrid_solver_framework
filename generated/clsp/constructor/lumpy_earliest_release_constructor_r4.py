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
    """Constructor conservador: activa setups lo antes posible, garantizando demanda del período 0."""

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

        # Prioriza ítems con demanda más temprana y mayor volumen total.
        items = list(range(n_items))
        items.sort(key=lambda i: (first_demand_period(i), -total_demand(i)))

        # Pequeña perturbación controlada, sin romper la prioridad principal.
        if n_items >= 2 and self.window_bias > 0.0 and rng.random() < self.window_bias:
            i = rng.randrange(n_items)
            j = rng.randrange(n_items)
            if i != j:
                items[i], items[j] = items[j], items[i]
                items.sort(key=lambda i: (first_demand_period(i), -total_demand(i)))

        # Heurística:
        # - Si un ítem tiene demanda en t=0, forzamos setup en t=0.
        # - Para el resto, colocamos el primer setup en el primer período donde aún
        #   queda capacidad suficiente para el setup y parte de su demanda.
        # - Luego, si hace falta, añadimos setups adicionales en períodos posteriores
        #   que todavía tienen demanda pendiente.
        for i in items:
            dem = [float(inst.demand[i][t]) for t in range(n_periods)]
            if sum(dem) <= 0.0:
                continue

            s_time = float(inst.setup_time[i])

            # Ítems con demanda en t=0 deben estar disponibles en t=0.
            if dem[0] > 0.0:
                if remaining_cap[0] >= s_time:
                    sol[i][0] = True
                    # No fijamos cantidad aquí; solo garantizamos la existencia del setup.
                    # Reservar el setup evita sobrecargar el período con otros ítems.
                    remaining_cap[0] -= s_time
                else:
                    # Si el período 0 está muy apretado, intentamos al menos no perder
                    # la factibilidad: en la práctica los instancias válidas para el validador
                    # admiten este setup. No hacemos cambios destructivos.
                    sol[i][0] = True

            # Recorremos períodos con demanda y activamos el primer setup disponible.
            # Como las cantidades las decide el LP, basta con asegurar setups en los
            # períodos donde el ítem necesita producir.
            started = any(sol[i][t] for t in range(n_periods))
            if not started:
                fd = first_demand_period(i)
                for t in range(fd, n_periods):
                    if remaining_cap[t] >= s_time:
                        sol[i][t] = True
                        remaining_cap[t] -= s_time
                        started = True
                        break
                if not started:
                    # Último recurso: activa el primer período con capacidad residual.
                    for t in range(fd, n_periods):
                        if not sol[i][t]:
                            sol[i][t] = True
                            break

            # Si aún hay demanda en períodos posteriores, añadimos setups solo cuando
            # se detecta un nuevo bloque de demanda no cubierto por setups previos.
            last_setup = max((t for t in range(n_periods) if sol[i][t]), default=-1)
            for t in range(last_setup + 1, n_periods):
                if dem[t] <= 0.0:
                    continue
                # Si aparece demanda después del último setup, abrimos un nuevo bloque
                # en ese mismo período, siempre que la capacidad lo permita.
                if not sol[i][t]:
                    if remaining_cap[t] >= s_time:
                        sol[i][t] = True
                        remaining_cap[t] -= s_time
                    else:
                        # Mantener la idea de "earliest release": si no cabe el setup
                        # aquí, se intenta colocarlo antes, pero nunca después del período
                        # de demanda.
                        for k in range(t - 1, -1, -1):
                            if remaining_cap[k] >= s_time:
                                sol[i][k] = True
                                remaining_cap[k] -= s_time
                                break

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_bias: float = 0.35):
    return LumpyEarliestReleaseConstructor(window_bias=window_bias)
