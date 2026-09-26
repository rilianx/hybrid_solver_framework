from __future__ import annotations

from typing import Iterable

from generated.cvrp_routes_cycle.model.parts import canonical

COMPONENT = {
    "name": "customer_relocate",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective"],
    "params": {
        "max_samples_per_route": {"type": "int", "range": [1, 20]},
    },
}


class CustomerRelocateNeighborhood:
    """Mueve un cliente a otra posición (misma ruta o distinta ruta).

    Movimiento extendido para garantizar undo exacto:
    (ri, pi, rj, pj, c, source_route)
    donde:
      - ri, pi: posición original del cliente c en la ruta fuente
      - rj, pj: inserción destino
      - c: cliente movido
      - source_route: tupla canónica original de la ruta fuente completa
    """

    def __init__(self, problem, max_samples_per_route: int = 6):
        self.problem = problem
        self.max_samples_per_route = int(max_samples_per_route)

    def moves(self, sol) -> Iterable[tuple]:
        sol = canonical(sol)
        for ri, route in enumerate(sol):
            source_route = tuple(route)
            for pi, c in enumerate(route):
                for rj, route2 in enumerate(sol):
                    limit = len(route2) + 1
                    if ri == rj:
                        limit = len(route2)
                    for pj in range(limit):
                        if ri == rj and (pj == pi or pj == pi + 1):
                            continue
                        yield (ri, pi, rj, pj, c, source_route)

    def apply(self, sol, m):
        ri, pi, rj, pj, c, source_route = m
        sol = canonical(sol)
        routes = [list(r) for r in sol]

        if ri < 0 or ri >= len(routes):
            return canonical(tuple(tuple(r) for r in routes))
        if pi < 0 or pi >= len(routes[ri]):
            return canonical(tuple(tuple(r) for r in routes))

        moved = routes[ri].pop(pi)

        # Conservador: si el movimiento no coincide con el cliente almacenado, usamos el extraído.
        c = moved

        if ri == rj and pj > pi:
            pj -= 1

        if 0 <= ri < len(routes) and not routes[ri]:
            del routes[ri]
            if rj > ri:
                rj -= 1

        if rj < 0:
            rj = 0
        if rj > len(routes):
            rj = len(routes)

        routes[rj].insert(pj, c)
        return canonical(tuple(tuple(r) for r in routes))

    def undo(self, sol, m):
        ri, pi, rj, pj, c, source_route = m
        sol = canonical(sol)
        routes = [list(r) for r in sol]

        # Eliminar el cliente movido allí donde esté
        found = False
        for k, route in enumerate(routes):
            for t, cust in enumerate(route):
                if cust == c:
                    route.pop(t)
                    found = True
                    if not route:
                        del routes[k]
                    break
            if found:
                break

        # Restaurar la ruta fuente original completa.
        # La ruta fuente sin c debe existir en el estado actual, salvo que fuera singleton.
        source_wo_c = tuple(x for x in source_route if x != c)
        restored = False
        for k, route in enumerate(routes):
            if tuple(route) == source_wo_c:
                routes[k] = list(source_route)
                restored = True
                break

        if not restored:
            # Si la ruta fuente era singleton, tras quitar c desaparece; simplemente la reinsertamos.
            routes.append(list(source_route))

        return canonical(tuple(tuple(r) for r in routes))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_samples_per_route: int = 6):
    return CustomerRelocateNeighborhood(problem, max_samples_per_route=max_samples_per_route)
