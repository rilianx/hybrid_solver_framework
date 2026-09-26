from __future__ import annotations

from typing import Iterable
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "or_opt_block",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "block_size": {"type": "int", "range": [1, 3]},
    },
}


class OrOptBlockNeighborhood:
    """Mueve un bloque consecutivo de 1..block_size clientes a otra posición.
    Movimiento = (block, p1, n1, p2, n2), donde block es una tupla de clientes.
    """

    def __init__(self, problem, block_size: int = 2):
        self.problem = problem
        self.block_size = block_size

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def moves(self, sol) -> Iterable[tuple]:
        routes = list(sol)
        for ri, r in enumerate(routes):
            L = len(r)
            for start in range(L):
                for length in range(1, min(self.block_size, L - start) + 1):
                    block = tuple(r[start : start + length])
                    p1 = r[start - 1] if start > 0 else 0
                    n1 = r[start + length] if start + length < L else 0
                    for rj, s in enumerate(routes):
                        for pj in range(len(s) + 1):
                            if ri == rj and start <= pj <= start + length:
                                continue
                            p2 = s[pj - 1] if pj > 0 else 0
                            n2 = s[pj] if pj < len(s) else 0
                            yield (block, p1, n1, p2, n2)

    def apply(self, sol, m):
        block, p1, n1, p2, n2 = m
        block = tuple(block)
        routes = self._as_lists(sol)

        src = None
        start = None
        for ri, r in enumerate(routes):
            for pi in range(len(r) - len(block) + 1):
                if tuple(r[pi : pi + len(block)]) == block:
                    src = ri
                    start = pi
                    break
            if src is not None:
                break

        if src is None:
            return canonical(routes)

        del routes[src][start : start + len(block)]
        if not routes[src]:
            routes.pop(src)

        inserted = False
        for r in routes:
            for pj in range(len(r) + 1):
                left = r[pj - 1] if pj > 0 else 0
                right = r[pj] if pj < len(r) else 0
                if left == p2 and right == n2:
                    for off, c in enumerate(block):
                        r.insert(pj + off, c)
                    inserted = True
                    break
            if inserted:
                break

        if not inserted:
            routes.append(list(block))

        return canonical(routes)

    def undo(self, sol, m):
        block, p1, n1, p2, n2 = m
        inverse = (block, p2, n2, p1, n1)
        return self.apply(sol, inverse)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem, block_size: int = 2):
    return OrOptBlockNeighborhood(problem, block_size=block_size)
