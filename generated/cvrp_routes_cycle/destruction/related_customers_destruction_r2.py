from __future__ import annotations

from random import Random
from typing import Any

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "related_customers_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RelatedCustomersDestruction:
    """Libera un racimo de clientes cercanos al depósito/entre sí."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _relatedness(self, a: int, b: int) -> float:
        # menor es mejor: distancia + diferencia de demanda
        return float(self.inst.dist(a, b)) + 0.1 * abs(float(self.inst.demand[a]) - float(self.inst.demand[b]))

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)

        routes = list(canonical(sol))
        if not routes:
            return assignment, set()

        n = int(self.inst.n_customers)
        target = max(1, min(n, int(round(ratio * n))))

        # Selección a nivel de ruta: libera rutas completas, no clientes sueltos.
        route_data = []
        for idx, route in enumerate(routes):
            if not route:
                continue
            route_customers = tuple(int(c) for c in route)
            demand = sum(float(self.inst.demand[c]) for c in route_customers)
            span = 0.0
            prev = 0
            for c in route_customers:
                span += float(self.inst.dist(prev, c))
                prev = c
            span += float(self.inst.dist(prev, 0))
            # rutas más largas / más cargadas primero, con un pequeño ruido para diversificar
            score = span + 0.05 * demand + 1e-6 * rng.random()
            route_data.append((score, idx, route_customers))

        route_data.sort(reverse=True)

        removed_customers: set[int] = set()
        selected_route_indices: set[int] = set()
        for _, idx, custs in route_data:
            if len(removed_customers) >= target:
                break
            selected_route_indices.add(idx)
            removed_customers.update(custs)

        if not removed_customers:
            # Fallback mínimo: una ruta cualquiera
            idx, custs = 0, tuple(int(c) for c in routes[0])
            selected_route_indices.add(idx)
            removed_customers.update(custs[:1])

        free_vars: set[str] = set()
        for name, val in assignment.items():
            if not name.startswith("x_"):
                continue
            parts = name.split("_")
            if len(parts) != 3:
                continue
            i, j = int(parts[1]), int(parts[2])
            if i in removed_customers or j in removed_customers:
                free_vars.add(name)

        # Si la formulación tiene variables de activación/uso por cliente,
        # liberamos también las asociadas a los clientes destruidos.
        for name in assignment:
            if name.startswith("y_"):
                suffix = name[2:]
                try:
                    c = int(suffix)
                except ValueError:
                    continue
                if c in removed_customers:
                    free_vars.add(name)

        # Asegura que al menos una variable de cada ruta seleccionada quede libre.
        if not free_vars:
            for name in assignment:
                if name.startswith("x_"):
                    parts = name.split("_")
                    if len(parts) == 3 and int(parts[1]) in removed_customers:
                        free_vars.add(name)
                        break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RelatedCustomersDestruction(problem, problem.inst)
