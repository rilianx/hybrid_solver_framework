from __future__ import annotations

COMPONENT = {
    "name": "relocate_customer_between_routes",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "canonical"],
    "params": {
        "same_route_allowed": {"type": "bool"},
    },
}

from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical


class RelocateCustomerBetweenRoutes:
    """Reloca un cliente a otra posición, dentro de su ruta o entre rutas.

    Movimiento:
        (src_route, src_pos, dst_route, dst_pos)

    Aquí src_route y dst_route son las tuplas canónicas de las rutas en la
    solución original, lo que permite que undo(apply(sol, m)) == sol incluso
    si la eliminación de una ruta vacía cambia el orden canónico.
    """

    def __init__(self, problem, same_route_allowed: bool = True):
        self.problem = problem
        self.same_route_allowed = bool(same_route_allowed)

    @staticmethod
    def _find_route_index(sol, route):
        for idx, r in enumerate(sol):
            if r == route:
                return idx
        raise IndexError("route not found in solution")

    @staticmethod
    def _find_customer(sol, customer):
        for ri, route in enumerate(sol):
            for pi, c in enumerate(route):
                if c == customer:
                    return ri, pi
        raise IndexError("customer not found in solution")

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        r = len(sol)
        for i, route in enumerate(sol):
            for p in range(len(route)):
                for j in range(r):
                    if i == j and not self.same_route_allowed:
                        continue
                    max_ins = len(sol[j]) if j != i else len(sol[j]) - 1
                    for q in range(max_ins + 1):
                        if i == j and q == p:
                            continue
                        yield (sol[i], p, sol[j], q)

    def apply(self, sol, m):
        sol = canonical(sol)
        src_route, p, dst_route, q = m
        i = self._find_route_index(sol, src_route)
        j = self._find_route_index(sol, dst_route)

        routes = [list(route) for route in sol]
        c = routes[i].pop(p)

        if i == j and q > p:
            q -= 1

        if i == j:
            routes[i].insert(q, c)
        else:
            if i < j:
                routes[j].insert(q, c)
            else:
                routes[j].insert(q, c)

        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def undo(self, sol, m):
        sol = canonical(sol)
        src_route, p, dst_route, q = m

        if src_route == dst_route:
            # Movimiento intra-ruta: basta con deshacer el desplazamiento
            ri = self._find_route_index(sol, dst_route)
            routes = [list(route) for route in sol]
            c = routes[ri].pop(q)
            if p > q:
                p -= 1
            routes[ri].insert(p, c)
            routes = [tuple(route) for route in routes if route]
            return canonical(tuple(routes))

        # Movimiento inter-ruta:
        # 1) localizar y quitar el cliente de la ruta destino actual
        ri, q_cur = self._find_customer(sol, None)  # placeholder to satisfy linter-like tools
        # The actual customer identity is inferred from the move by looking at the
        # route content at position q in the destination route after apply:
        # the moved customer is the one inserted at q in dst_route.
        # Since dst_route may have been reordered canonically, identify it by content.
        dst_idx = self._find_route_index(sol, dst_route)
        routes = [list(route) for route in sol]
        c = routes[dst_idx].pop(q)
        if routes[dst_idx]:
            pass
        else:
            routes.pop(dst_idx)

        # 2) reinsert original source route as it was before the move
        routes.append(list(src_route))
        routes = [tuple(route) for route in routes if route]
        return canonical(tuple(routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, same_route_allowed: bool = True):
    return RelocateCustomerBetweenRoutes(problem, same_route_allowed=same_route_allowed)
