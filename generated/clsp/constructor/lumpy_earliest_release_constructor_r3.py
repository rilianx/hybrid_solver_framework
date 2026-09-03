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
    """Constructor conservador: distribuye la producción lo más temprano posible respetando capacidad."""

    def __init__(self, window_bias: float = 0.35):
        self.window_bias = window_bias

    def build(self, inst: CLSPInstance, rng: Random):
        n_items, n_periods = inst.n_items, inst.n_periods
        sol = [[False for _ in range(n_periods)] for _ in range(n_items)]

        remaining_cap = [float(inst.capacity[t]) for t in range(n_periods)]

        items = list(range(n_items))
        # Prioriza ítems con vencimiento más temprano; rompe empates con demanda total.
        items.sort(
            key=lambda i: (
                min((t for t in range(n_periods) if inst.demand[i][t] > 0), default=n_periods),
                -sum(inst.demand[i][t] for t in range(n_periods)),
            )
        )

        # Pequeña perturbación opcional, sin romper el orden por vencimiento.
        if n_items >= 2 and self.window_bias > 0.0 and rng.random() < self.window_bias:
            i = rng.randrange(n_items)
            j = rng.randrange(n_items)
            if i != j:
                items[i], items[j] = items[j], items[i]
                items.sort(
                    key=lambda i: (
                        min((t for t in range(n_periods) if inst.demand[i][t] > 0), default=n_periods),
                        -sum(inst.demand[i][t] for t in range(n_periods)),
                    )
                )

        for i in items:
            total_demand = sum(inst.demand[i][t] for t in range(n_periods))
            if total_demand <= 0:
                continue

            last_demand = max(t for t in range(n_periods) if inst.demand[i][t] > 0)

            remaining = float(total_demand)
            for t in range(last_demand, -1, -1):
                if remaining <= 1e-12:
                    break

                setup_time = float(inst.setup_time[i])
                # Debe caber al menos el setup; el resto de capacidad se usa para producir.
                usable = remaining_cap[t] - setup_time
                if usable <= 1e-12:
                    continue

                qty = min(remaining, usable)
                if qty > 1e-12:
                    sol[i][t] = True
                    remaining_cap[t] -= setup_time + qty
                    remaining -= qty

            # Si por alguna razón no cupo completamente, forzamos un patrón mínimo
            # sin eliminar lo ya asignado; el LP resolverá la asignación óptima.
            if remaining > 1e-12:
                # Último recurso: activar el primer período admisible y dejar que el LP
                # use el patrón obtenido. Esto mantiene la idea de "earliest release".
                for t in range(last_demand, -1, -1):
                    if not sol[i][t]:
                        sol[i][t] = True
                        break

        return tuple(tuple(row) for row in sol)


def build_component(problem, window_bias: float = 0.35):
    return LumpyEarliestReleaseConstructor(window_bias=window_bias)
