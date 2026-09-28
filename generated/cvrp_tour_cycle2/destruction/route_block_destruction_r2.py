from random import Random
from typing import Any

COMPONENT = {
    "name": "route_block_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RouteBlockDestruction:
    """Libera un bloque contiguo de una ruta del gran tour, rompiendo un segmento entero."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _routes_from_assignment(self, assignment: dict[str, float]) -> list[list[int]]:
        succ: dict[int, int] = {}
        starts: list[int] = []
        for var, val in assignment.items():
            if not var.startswith("x_") or val <= 0.5:
                continue
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            succ[ii] = jj
            if ii == 0 and jj != 0:
                starts.append(jj)

        routes: list[list[int]] = []
        used: set[int] = set()
        for s in starts:
            if s in used:
                continue
            route: list[int] = []
            cur = s
            while cur != 0 and cur not in used:
                route.append(cur)
                used.add(cur)
                cur = succ.get(cur, 0)
            if route:
                routes.append(route)

        for c in self.inst.customers:
            if c not in used:
                routes.append([c])
        return routes

    def _route_cost(self, route: list[int]) -> float:
        if not route:
            return 0.0
        total = self.inst.dist(0, route[0])
        for a, b in zip(route, route[1:]):
            total += self.inst.dist(a, b)
        total += self.inst.dist(route[-1], 0)
        return total

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = self._routes_from_assignment(assignment)
        x_vars = [v for v in assignment if v.startswith("x_")]
        if not routes:
            if x_vars:
                free_vars = {x_vars[0]}
                partial = {v: val for v, val in assignment.items() if v not in free_vars}
                return partial, free_vars
            return assignment, set()

        # Prioriza rutas largas/caras, pero destruye solo un bloque contiguo dentro de una ruta.
        scored = [(self._route_cost(route), len(route), idx) for idx, route in enumerate(routes)]
        scored.sort(reverse=True)

        target_route = routes[scored[0][2]]

        # Tamaño del bloque: proporcional a ratio, pero acotado a un segmento compacto.
        block_len = max(1, int(round(ratio * len(target_route))))
        block_len = min(block_len, len(target_route))

        if len(target_route) == 1:
            chosen_nodes = set(target_route)
        else:
            # Sesgo leve hacia bloques centrales para romper el patrón de decodificación,
            # pero manteniendo movimiento elemental de un solo segmento.
            max_start = len(target_route) - block_len
            if max_start <= 0:
                start = 0
            else:
                # Elegimos entre posiciones factibles con preferencia aleatoria.
                start = rng.randint(0, max_start)
            chosen_nodes = set(target_route[start : start + block_len])

        free_vars: set[str] = set()
        for var in x_vars:
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            # Se liberan los arcos que entran o salen del bloque contiguo.
            if ii in chosen_nodes or jj in chosen_nodes:
                free_vars.add(var)

        if not free_vars and x_vars:
            free_vars.add(x_vars[0])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return RouteBlockDestruction(problem, problem.inst)
