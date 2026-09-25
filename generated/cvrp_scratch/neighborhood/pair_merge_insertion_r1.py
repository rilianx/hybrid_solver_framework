from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "pair_merge_insertion",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst", "canonical"],
    "params": {},
}


class PairMergeInsertionNeighborhood:
    """Fusiona dos clientes en una sola ruta corta.
    Movimiento: (c1, p1, n1, c2, p2, n2, order)
    donde c1 y c2 se eliminan de sus rutas originales y se crean una ruta de dos clientes.
    order=0 -> (c1, c2), order=1 -> (c2, c1)
    """

    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst

    def _remove_one(self, routes, c):
        for ridx, r in enumerate(routes):
            if c in r:
                i = r.index(c)
                p = r[i - 1] if i > 0 else 0
                n = r[i + 1] if i + 1 < len(r) else 0
                r.pop(i)
                if not r:
                    routes.pop(ridx)
                return p, n
        raise ValueError("customer not found")

    def moves(self, sol) -> Iterable[tuple]:
        for i, r1 in enumerate(sol):
            for j, c1 in enumerate(r1):
                p1 = r1[j - 1] if j > 0 else 0
                n1 = r1[j + 1] if j + 1 < len(r1) else 0
                for k in range(i + 1, len(sol)):
                    r2 = sol[k]
                    for l, c2 in enumerate(r2):
                        p2 = r2[l - 1] if l > 0 else 0
                        n2 = r2[l + 1] if l + 1 < len(r2) else 0
                        yield (c1, p1, n1, c2, p2, n2, 0)
                        yield (c1, p1, n1, c2, p2, n2, 1)

    def apply(self, sol, m):
        c1, p1, n1, c2, p2, n2, order = m
        routes = [list(r) for r in sol]
        self._remove_one(routes, c1)
        self._remove_one(routes, c2)
        new_route = (c1, c2) if order == 0 else (c2, c1)
        routes.append(list(new_route))
        return canonical(routes)

    def undo(self, sol, m):
        c1, p1, n1, c2, p2, n2, order = m
        routes = [list(r) for r in sol]
        # remove the merged route
        for ridx, r in enumerate(routes):
            if len(r) == 2 and ((r[0], r[1]) == (c1, c2) or (r[0], r[1]) == (c2, c1)):
                routes.pop(ridx)
                break
        else:
            raise ValueError("merged route not found")
        # restore the original routes
        if p1 == 0 and n1 == 0:
            routes.append([c1])
        else:
            for ridx, r in enumerate(routes):
                if p1 == 0 and r and r[0] == n1:
                    r.insert(0, c1)
                    break
                for t in range(len(r) - 1):
                    if r[t] == p1 and r[t + 1] == n1:
                        r.insert(t + 1, c1)
                        break
                else:
                    continue
                break
        if p2 == 0 and n2 == 0:
            routes.append([c2])
        else:
            for ridx, r in enumerate(routes):
                if p2 == 0 and r and r[0] == n2:
                    r.insert(0, c2)
                    break
                for t in range(len(r) - 1):
                    if r[t] == p2 and r[t + 1] == n2:
                        r.insert(t + 1, c2)
                        break
                else:
                    continue
                break
        return canonical(routes)

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, **params):
    return PairMergeInsertionNeighborhood(problem)
