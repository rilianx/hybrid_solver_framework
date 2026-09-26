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
    """Elimina nodos de varias rutas, priorizando clientes caros dentro de cada ruta."""

    def __init__(self, problem, inst, ratio: float = 0.2):
        self.problem = problem
        self.inst = inst
        self.ratio = ratio

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

    def _customer_detour(self, route: list[int], pos: int) -> float:
        c = route[pos]
        prev_c = 0 if pos == 0 else route[pos - 1]
        next_c = 0 if pos + 1 == len(route) else route[pos + 1]
        return self.inst.dist(prev_c, c) + self.inst.dist(c, next_c) - self.inst.dist(prev_c, next_c)

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

        total_customers = sum(len(r) for r in routes)
        target = max(1, int(round(ratio * total_customers)))

        # Elegimos varias rutas, y dentro de cada una liberamos el cliente más "caro"
        # (mayor detour local). Esto produce una destrucción dispersa, no contigua.
        route_order = list(range(len(routes)))
        route_order.sort(key=lambda idx: (self._route_cost(routes[idx]), len(routes[idx])), reverse=True)

        chosen_customers: set[int] = set()
        for ridx in route_order:
            route = routes[ridx]
            if not route:
                continue
            if len(chosen_customers) >= target:
                break

            best_pos = 0
            best_score = None
            for pos in range(len(route)):
                score = self._customer_detour(route, pos)
                if best_score is None or score > best_score:
                    best_score = score
                    best_pos = pos

            chosen_customers.add(route[best_pos])

            if len(chosen_customers) >= target:
                break

        # Si el ratio pide más, añadimos clientes de rutas distintas, uno por ruta,
        # en orden aleatorio entre las mejores rutas.
        if len(chosen_customers) < target:
            extra_order = route_order[:]
            rng.shuffle(extra_order)
            for ridx in extra_order:
                route = routes[ridx]
                for c in route:
                    if c not in chosen_customers:
                        chosen_customers.add(c)
                        break
                if len(chosen_customers) >= target:
                    break

        free_vars: set[str] = set()
        for var in x_vars:
            _, i, j = var.split("_")
            ii, jj = int(i), int(j)
            if ii in chosen_customers or jj in chosen_customers:
                free_vars.add(var)

        if not free_vars and x_vars:
            free_vars.add(x_vars[0])

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return RouteBlockDestruction(problem, problem.inst, ratio=ratio)
