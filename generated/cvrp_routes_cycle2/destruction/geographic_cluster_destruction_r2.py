from __future__ import annotations

from math import hypot
from random import Random
from typing import Any


COMPONENT = {
    "name": "geographic_cluster_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "problem.inst coordinates"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class GeographicClusterDestruction:
    """Libera rutas completas cercanas a una semilla geográfica.

    A diferencia de una destrucción por arcos, aquí la unidad de destrucción es
    la ruta completa: se elige un cliente semilla, se localiza la ruta que lo
    contiene y se liberan todas las variables asociadas a esa ruta, junto con
    rutas vecinas en el plano hasta cubrir la fracción pedida.
    """

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _coord(self, c: int) -> tuple[float, float]:
        x = self.inst.x[c] if hasattr(self.inst, "x") else self.inst.coords[c][0]
        y = self.inst.y[c] if hasattr(self.inst, "y") else self.inst.coords[c][1]
        return float(x), float(y)

    def _route_centroid(self, route) -> tuple[float, float]:
        if not route:
            return 0.0, 0.0
        xs = ys = 0.0
        for c in route:
            x, y = self._coord(int(c))
            xs += x
            ys += y
        m = float(len(route))
        return xs / m, ys / m

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = dict(self.problem.to_assignment(sol))
        x_vars = [name for name in assignment if name.startswith("x_")]
        if not x_vars:
            return assignment, set()

        routes = list(sol) if sol is not None else []
        if not routes:
            return assignment, set()

        # Elegir una ruta semilla por un cliente aleatorio y expandir por cercanía
        all_customers = [c for route in routes for c in route]
        if not all_customers:
            return assignment, set()

        seed_customer = rng.choice(all_customers)
        seed_route_idx = None
        for idx, route in enumerate(routes):
            if seed_customer in route:
                seed_route_idx = idx
                break
        if seed_route_idx is None:
            seed_route_idx = 0

        centroids = [self._route_centroid(route) for route in routes]
        sx, sy = centroids[seed_route_idx]

        route_order = []
        for idx, (cx, cy) in enumerate(centroids):
            route_order.append((hypot(cx - sx, cy - sy), idx))
        route_order.sort()

        total_customers = sum(len(route) for route in routes)
        target_customers = max(1, int(round(ratio * max(1, total_customers))))

        freed_routes = set()
        freed_customers = 0
        for _, idx in route_order:
            freed_routes.add(idx)
            freed_customers += len(routes[idx])
            if freed_customers >= target_customers:
                break

        freed_customer_set = set()
        for idx in freed_routes:
            freed_customer_set.update(routes[idx])

        free_vars = set()
        for name in x_vars:
            parts = name.split("_")
            if len(parts) == 3:
                try:
                    i, j = int(parts[1]), int(parts[2])
                except ValueError:
                    continue
                if i in freed_customer_set or j in freed_customer_set:
                    free_vars.add(name)

        if not free_vars:
            free_vars = {rng.choice(x_vars)}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return GeographicClusterDestruction(problem, problem.inst)
