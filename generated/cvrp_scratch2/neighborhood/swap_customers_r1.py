from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "swap_customers",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "max_candidates": {"type": "int", "range": [1, 50]},
    },
}


class SwapCustomersNeighborhood:
    """Intercambia dos clientes, estén en la misma ruta o en rutas distintas.
    Movimiento = (c1, p1, n1, c2, p2, n2), guardando vecinos originales para deshacer.
    """

    def __init__(self, problem, max_candidates: int = 20):
        self.problem = problem
        self.max_candidates = max_candidates

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def moves(self, sol) -> Iterable[tuple]:
        all_customers = [c for r in sol for c in r]
        pos = {}
        for ri, r in enumerate(sol):
            for pi, c in enumerate(r):
                pos[c] = (ri, pi)
        for i, c1 in enumerate(all_customers):
            ri, pi = pos[c1]
            p1 = sol[ri][pi - 1] if pi > 0 else 0
            n1 = sol[ri][pi + 1] if pi + 1 < len(sol[ri]) else 0
            for c2 in all_customers[i + 1 :]:
                rj, pj = pos[c2]
                p2 = sol[rj][pj - 1] if pj > 0 else 0
                n2 = sol[rj][pj + 1] if pj + 1 < len(sol[rj]) else 0
                yield (c1, p1, n1, c2, p2, n2)

    def apply(self, sol, m):
        c1, p1, n1, c2, p2, n2 = m
        routes = self._as_lists(sol)

        loc = {}
        for ri, r in enumerate(routes):
            for pi, c in enumerate(r):
                loc[c] = (ri, pi)

        if c1 not in loc or c2 not in loc or c1 == c2:
            return canonical(routes)

        (r1, i1) = loc[c1]
        (r2, i2) = loc[c2]

        if r1 == r2 and i1 == i2:
            return canonical(routes)

        routes[r1][i1], routes[r2][i2] = routes[r2][i2], routes[r1][i1]
        return canonical(routes)

    def undo(self, sol, m):
        c1, p1, n1, c2, p2, n2 = m
        return self.apply(sol, (c1, p2, n2, c2, p1, n1))

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_candidates: int = 20):
    return SwapCustomersNeighborhood(problem, max_candidates=max_candidates)
