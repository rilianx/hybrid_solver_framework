from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "or_opt_block",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "block_size": {"type": "int", "range": [2, 10]},
    },
}


class OrOptBlockNeighborhood:
    """2-opt intra-ruta sobre un bloque consecutivo: revierte un segmento de clientes.

    Movimiento = (route, i, j, a, b, c, d), donde:
      - route identifica la ruta afectada por su contenido actual,
      - i, j delimitan el segmento r[i:j+1] a invertir,
      - a = predecesor de r[i], b = r[i], c = r[j], d = sucesor de r[j],
        usando 0 para el depósito.
    """

    def __init__(self, problem, block_size: int = 4):
        self.problem = problem
        self.block_size = block_size

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def _route_signature(self, r):
        return tuple(r)

    def moves(self, sol) -> Iterable[tuple]:
        for r in sol:
            L = len(r)
            if L < 2:
                continue
            max_len = min(self.block_size, L)
            for i in range(L - 1):
                for j in range(i + 1, min(L, i + max_len)):
                    a = r[i - 1] if i > 0 else 0
                    b = r[i]
                    c = r[j]
                    d = r[j + 1] if j + 1 < L else 0
                    yield (self._route_signature(r), i, j, a, b, c, d)

    def apply(self, sol, m):
        route_sig, i, j, a, b, c, d = m
        routes = self._as_lists(sol)

        target_idx = None
        for idx, r in enumerate(routes):
            if tuple(r) == route_sig:
                target_idx = idx
                break

        if target_idx is None:
            return canonical(routes)

        r = routes[target_idx]
        if not (0 <= i < j < len(r)):
            return canonical(routes)

        # Reversión del segmento interno [i, j]
        r[i : j + 1] = reversed(r[i : j + 1])
        return canonical(routes)

    def undo(self, sol, m):
        # La reversión es auto-inversa
        return self.apply(sol, m)

    def delta(self, sol, m):
        route_sig, i, j, a, b, c, d = m
        inst = self.problem.inst

        # El segmento invertido no cambia aristas internas de forma relevante;
        # solo cambian las cuatro conexiones frontera:
        # antes: a-ब, c-d
        # después: a-c, b-d
        before = inst.dist(a, b) + inst.dist(c, d)
        after = inst.dist(a, c) + inst.dist(b, d)
        return after - before


def build_component(problem, block_size: int = 4):
    return OrOptBlockNeighborhood(problem, block_size=block_size)
