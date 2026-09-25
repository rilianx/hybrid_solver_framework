from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "relocate_customer",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_candidates": {"type": "int", "range": [1, 50]},
    },
}


class RelocateCustomerNeighborhood:
    """Mueve un cliente a otra posición (o a otra ruta) preservando el resto.
    Movimiento = (c, p1, n1, p2, n2), donde p1/n1 son vecinos en la ruta origen
    y p2/n2 indican el hueco de inserción destino.
    """

    def __init__(self, problem, max_candidates: int = 20):
        self.problem = problem
        self.max_candidates = max_candidates

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def _find(self, routes, c):
        for ri, r in enumerate(routes):
            for pi, x in enumerate(r):
                if x == c:
                    return ri, pi
        raise ValueError("cliente no encontrado")

    def moves(self, sol) -> Iterable[tuple]:
        routes = list(sol)
        for ri, r in enumerate(routes):
            if not r:
                continue
            for pi, c in enumerate(r):
                p1 = r[pi - 1] if pi > 0 else 0
                n1 = r[pi + 1] if pi + 1 < len(r) else 0
                for rj, s in enumerate(routes):
                    for pj in range(len(s) + 1):
                        if ri == rj and (pj == pi or pj == pi + 1):
                            continue
                        p2 = s[pj - 1] if pj > 0 else 0
                        n2 = s[pj] if pj < len(s) else 0
                        yield (c, p1, n1, p2, n2)

    def apply(self, sol, m):
        c, p1, n1, p2, n2 = m
        routes = self._as_lists(sol)

        # remove c from its route
        src_ri = src_pi = None
        for ri, r in enumerate(routes):
            for pi, x in enumerate(r):
                if x == c:
                    src_ri, src_pi = ri, pi
                    break
            if src_ri is not None:
                break
        if src_ri is None:
            return canonical(routes)

        routes[src_ri].pop(src_pi)
        if not routes[src_ri]:
            routes.pop(src_ri)

        # insert at destination using neighbour hints
        inserted = False
        for r in routes:
            if not r:
                continue
            for pj in range(len(r) + 1):
                left = r[pj - 1] if pj > 0 else 0
                right = r[pj] if pj < len(r) else 0
                if left == p2 and right == n2:
                    r.insert(pj, c)
                    inserted = True
                    break
            if inserted:
                break

        if not inserted:
            # destination may be an empty spot created by deleting the source route
            if p2 == 0 and n2 == 0:
                routes.append([c])
            else:
                routes.append([c])

        return canonical(routes)

    def undo(self, sol, m):
        c, p1, n1, p2, n2 = m
        inverse = (c, p2, n2, p1, n1)
        return self.apply(sol, inverse)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_candidates: int = 20):
    return RelocateCustomerNeighborhood(problem, max_candidates=max_candidates)
