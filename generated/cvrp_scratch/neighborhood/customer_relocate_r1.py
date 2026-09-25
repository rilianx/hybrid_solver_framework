from __future__ import annotations

from typing import Iterable, Sequence
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "customer_relocate",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst", "canonical"],
    "params": {},
}


class CustomerRelocateNeighborhood:
    """Mueve un cliente a otra posición o ruta.
    Movimiento: (c, p, n, a, b) donde c está entre p-n y se inserta entre a-b.
    0 representa el depósito.
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _find_route(self, sol, prev, cur, nxt):
        for ridx, r in enumerate(sol):
            if cur not in r:
                continue
            i = r.index(cur)
            rp = r[i - 1] if i > 0 else 0
            rn = r[i + 1] if i + 1 < len(r) else 0
            if rp == prev and rn == nxt:
                return ridx, i
        raise ValueError("move does not match solution")

    def _remove_insert(self, sol, c, p, n, a, b):
        routes = [list(r) for r in sol]
        ridx_s, i = self._find_route(sol, p, c, n)
        routes[ridx_s].pop(i)
        if not routes[ridx_s]:
            routes.pop(ridx_s)

        # insert into target route gap (a,b)
        inserted = False
        for ridx_t, r in enumerate(routes):
            if a == 0 and (r and r[0] == b):
                routes[ridx_t].insert(0, c)
                inserted = True
                break
            for j in range(len(r) - 1):
                if r[j] == a and r[j + 1] == b:
                    routes[ridx_t].insert(j + 1, c)
                    inserted = True
                    break
            if inserted:
                break
            if r and r[-1] == a and b == 0:
                routes[ridx_t].append(c)
                inserted = True
                break

        if not inserted:
            if a == 0 and b == 0:
                routes.append([c])
            else:
                raise ValueError("insert gap not found")
        return canonical(routes)

    def moves(self, sol) -> Iterable[tuple]:
        routes = sol
        for r_idx, r in enumerate(routes):
            for i, c in enumerate(r):
                p = r[i - 1] if i > 0 else 0
                n = r[i + 1] if i + 1 < len(r) else 0
                for s_idx, s in enumerate(routes):
                    if s_idx == r_idx:
                        continue
                    if not s:
                        continue
                    # before first
                    yield (c, p, n, 0, s[0])
                    # between
                    for j in range(len(s) - 1):
                        yield (c, p, n, s[j], s[j + 1])
                    # after last
                    yield (c, p, n, s[-1], 0)

    def apply(self, sol, m):
        c, p, n, a, b = m
        return self._remove_insert(sol, c, p, n, a, b)

    def undo(self, sol, m):
        c, p, n, a, b = m
        return self._remove_insert(sol, c, a, b, p, n)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return CustomerRelocateNeighborhood(problem)
