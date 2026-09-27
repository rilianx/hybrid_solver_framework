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

        routes = [tuple(int(c) for c in route) for route in canonical(sol)]
        if not routes:
            return assignment, set()

        n = int(self.inst.n_customers)
        target = max(1, min(n, int(round(ratio * n))))

        # Distinta a una destrucción aleatoria de clientes:
        # 1) elegimos una ruta semilla "cara" (larga/cargada),
        # 2) ampliamos a la ruta más relacionada con ella,
        # 3) liberamos clientes completos de esas rutas hasta alcanzar el objetivo.
        route_info = []
        for idx, route in enumerate(routes):
            if not route:
                continue
            demand = sum(float(self.inst.demand[c]) for c in route)
            route_len = 0.0
            prev = 0
            for c in route:
                route_len += float(self.inst.dist(prev, c))
                prev = c
            route_len += float(self.inst.dist(prev, 0))
            score = route_len + 0.05 * demand + 1e-6 * rng.random()
            route_info.append((score, idx, route))

        if not route_info:
            return assignment, set()

        route_info.sort(reverse=True)
        seed_score, seed_idx, seed_route = route_info[0]

        def route_distance(r1: tuple[int, ...], r2: tuple[int, ...]) -> float:
            # distancia entre rutas por sus extremos y su demanda media
            if not r1 or not r2:
                return float("inf")
            a1, b1 = r1[0], r1[-1]
            a2, b2 = r2[0], r2[-1]
            d = min(
                float(self.inst.dist(a1, a2)),
                float(self.inst.dist(a1, b2)),
                float(self.inst.dist(b1, a2)),
                float(self.inst.dist(b1, b2)),
            )
            dem1 = sum(float(self.inst.demand[c]) for c in r1)
            dem2 = sum(float(self.inst.demand[c]) for c in r2)
            return d + 0.05 * abs(dem1 - dem2)

        # Ordena las demás rutas por relación con la semilla.
        related_routes = [(0.0, seed_idx, seed_route)]
        for _, idx, route in route_info[1:]:
            related_routes.append((route_distance(seed_route, route), idx, route))
        related_routes.sort(key=lambda t: t[0])

        removed_customers: set[int] = set()
        selected_route_indices: set[int] = set()

        for _, idx, route in related_routes:
            if len(removed_customers) >= target:
                break
            selected_route_indices.add(idx)
            for c in route:
                removed_customers.add(int(c))
                if len(removed_customers) >= target:
                    break

        if not removed_customers:
            removed_customers.add(int(seed_route[0]))

        free_vars: set[str] = set()
        for name in assignment:
            if name.startswith("x_"):
                parts = name.split("_")
                if len(parts) == 3:
                    try:
                        i, j = int(parts[1]), int(parts[2])
                    except ValueError:
                        continue
                    if i in removed_customers or j in removed_customers:
                        free_vars.add(name)
            elif name.startswith("y_"):
                suffix = name[2:]
                try:
                    c = int(suffix)
                except ValueError:
                    continue
                if c in removed_customers:
                    free_vars.add(name)

        if not free_vars:
            for name in assignment:
                if name.startswith("x_"):
                    parts = name.split("_")
                    if len(parts) == 3:
                        try:
                            i = int(parts[1])
                        except ValueError:
                            continue
                        if i in removed_customers:
                            free_vars.add(name)
                            break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RelatedCustomersDestruction(problem, problem.inst)
