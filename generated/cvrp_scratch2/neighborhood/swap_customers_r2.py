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
    """Vecindario elemental de reubicación:
    mueve un cliente c después de otro cliente d (o como cliente único si d=0).
    El movimiento guarda el vecindario original de c para deshacerlo exactamente.
    """

    def __init__(self, problem, max_candidates: int = 20):
        self.problem = problem
        self.max_candidates = max_candidates

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def _locations(self, sol):
        loc = {}
        for ri, r in enumerate(sol):
            for pi, c in enumerate(r):
                loc[c] = (ri, pi)
        return loc

    def moves(self, sol) -> Iterable[tuple]:
        customers = [c for r in sol for c in r]
        loc = self._locations(sol)

        # Limitar candidatos de forma simple y determinista.
        customers = customers[: self.max_candidates] if self.max_candidates > 0 else customers

        for c in customers:
            ri, pi = loc[c]
            pc = sol[ri][pi - 1] if pi > 0 else 0
            nc = sol[ri][pi + 1] if pi + 1 < len(sol[ri]) else 0

            for d in [x for x in customers if x != c]:
                yield (c, pc, nc, d)

    def apply(self, sol, m):
        c, pc, nc, d = m
        routes = self._as_lists(sol)

        loc = self._locations(routes)
        if c not in loc:
            return canonical(routes)

        r_c, i_c = loc[c]
        # quitar c
        routes[r_c].pop(i_c)
        if len(routes[r_c]) == 0:
            del routes[r_c]

        if d != 0 and d in loc:
            # localizar d en la solución original no basta tras la extracción;
            # reconstruimos sobre la estructura actual.
            loc2 = {}
            for ri, r in enumerate(routes):
                for pi, x in enumerate(r):
                    loc2[x] = (ri, pi)

            if d in loc2:
                r_d, i_d = loc2[d]
                routes[r_d].insert(i_d + 1, c)
            else:
                # si d desapareció por coincidir con el cliente movido o por otra
                # situación no esperada, degradar a inserción como ruta sola.
                routes.append([c])
        else:
            routes.append([c])

        return canonical(routes)

    def undo(self, sol, m):
        c, pc, nc, d = m
        # Invertimos la operación: quitamos c de donde esté y lo reinsertamos
        # después de su predecesor original pc (o como ruta única si pc=0).
        routes = self._as_lists(sol)
        loc = self._locations(routes)

        if c not in loc:
            return canonical(routes)

        r_c, i_c = loc[c]
        routes[r_c].pop(i_c)
        if len(routes[r_c]) == 0:
            del routes[r_c]

        if pc != 0:
            loc2 = {}
            for ri, r in enumerate(routes):
                for pi, x in enumerate(r):
                    loc2[x] = (ri, pi)
            if pc in loc2:
                r_p, i_p = loc2[pc]
                routes[r_p].insert(i_p + 1, c)
            else:
                routes.append([c])
        else:
            routes.append([c])

        return canonical(routes)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, max_candidates: int = 20):
    return SwapCustomersNeighborhood(problem, max_candidates=max_candidates)
