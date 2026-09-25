from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "two_customer_chain_merge",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst", "canonical"],
    "params": {},
}


class TwoCustomerChainMergeNeighborhood:
    """Movimiento elemental: extrae dos clientes y los re-inserta como cadena en un arco.

    Movimiento: (a, pa, na, b, pb, nb, u, v, order)
    - a y b son los clientes extraídos
    - (pa, na) y (pb, nb) describen la posición original de cada cliente
    - (u, v) es el arco de inserción de la cadena
    - order=0 inserta (a, b), order=1 inserta (b, a)
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _find_customer(self, routes, c):
        for ridx, r in enumerate(routes):
            for idx, x in enumerate(r):
                if x == c:
                    p = r[idx - 1] if idx > 0 else 0
                    n = r[idx + 1] if idx + 1 < len(r) else 0
                    return ridx, idx, p, n
        raise ValueError("customer not found")

    def _remove_customer(self, routes, c):
        for ridx, r in enumerate(routes):
            if c in r:
                r.remove(c)
                if not r:
                    routes.pop(ridx)
                return
        raise ValueError("customer not found for removal")

    def _insert_customer(self, routes, c, p, n):
        if p == 0 and n == 0:
            routes.append([c])
            return

        if p == 0:
            for r in routes:
                if r and r[0] == n:
                    r.insert(0, c)
                    return
            routes.append([c])
            return

        for r in routes:
            for j in range(len(r) - 1):
                if r[j] == p and r[j + 1] == n:
                    r.insert(j + 1, c)
                    return
            if r and r[-1] == p and n == 0:
                r.append(c)
                return

        routes.append([c])

    def moves(self, sol) -> Iterable[tuple]:
        routes = sol
        for i, r1 in enumerate(routes):
            for j, a in enumerate(r1):
                pa = r1[j - 1] if j > 0 else 0
                na = r1[j + 1] if j + 1 < len(r1) else 0
                for k in range(i, len(routes)):
                    r2 = routes[k]
                    start = j + 1 if k == i else 0
                    for l in range(start, len(r2)):
                        b = r2[l]
                        if i == k and a == b:
                            continue
                        pb = r2[l - 1] if l > 0 else 0
                        nb = r2[l + 1] if l + 1 < len(r2) else 0
                        for t_idx, t in enumerate(routes):
                            if t_idx in (i, k) or not t:
                                continue
                            yield (a, pa, na, b, pb, nb, 0, 0, 0)
                            yield (a, pa, na, b, pb, nb, t[0], t[0], 0)
                            yield (a, pa, na, b, pb, nb, t[-1], t[-1], 1)
                            for z in range(len(t) - 1):
                                yield (a, pa, na, b, pb, nb, t[z], t[z + 1], 0)

    def apply(self, sol, m):
        a, pa, na, b, pb, nb, u, v, order = m
        routes = [list(r) for r in sol]

        self._find_customer(routes, a)
        self._find_customer(routes, b)
        self._remove_customer(routes, a)
        self._remove_customer(routes, b)

        chain = (a, b) if order == 0 else (b, a)
        inserted = False

        for r in routes:
            if u == 0 and r and r[0] == v:
                r.insert(0, chain[0])
                r.insert(1, chain[1])
                inserted = True
                break
            for j in range(len(r) - 1):
                if r[j] == u and r[j + 1] == v:
                    r.insert(j + 1, chain[0])
                    r.insert(j + 2, chain[1])
                    inserted = True
                    break
            if inserted:
                break
            if r and r[-1] == u and v == 0:
                r.extend([chain[0], chain[1]])
                inserted = True
                break

        if not inserted:
            routes.append(list(chain))

        return canonical(routes)

    def undo(self, sol, m):
        a, pa, na, b, pb, nb, u, v, order = m
        routes = [list(r) for r in sol]
        chain = (a, b) if order == 0 else (b, a)

        removed = False
        for ridx, r in enumerate(routes):
            for j in range(len(r) - 1):
                if r[j] == chain[0] and r[j + 1] == chain[1]:
                    r.pop(j + 1)
                    r.pop(j)
                    if not r:
                        routes.pop(ridx)
                    removed = True
                    break
            if removed:
                break
        if not removed:
            for ridx, r in enumerate(routes):
                if len(r) == 2 and tuple(r) == chain:
                    routes.pop(ridx)
                    removed = True
                    break

        if na == b:
            self._insert_customer(routes, a, pa, na)
            self._insert_customer(routes, b, pb, nb)
        elif nb == a:
            self._insert_customer(routes, b, pb, nb)
            self._insert_customer(routes, a, pa, na)
        else:
            self._insert_customer(routes, a, pa, na)
            self._insert_customer(routes, b, pb, nb)

        return canonical(routes)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return TwoCustomerChainMergeNeighborhood(problem)
