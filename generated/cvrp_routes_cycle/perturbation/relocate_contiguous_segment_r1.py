from __future__ import annotations

from random import Random
from typing import List, Tuple

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "relocate_contiguous_segment",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 20.0]}
    },
}


class RelocateContiguousSegment:
    def __init__(self, problem):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        sol = canonical(sol)
        if not sol:
            return sol

        routes = [list(route) for route in sol]
        non_empty = [idx for idx, r in enumerate(routes) if r]
        if not non_empty:
            return sol

        src_idx = rng.choice(non_empty)
        src = routes[src_idx]
        n = len(src)
        seg_len = max(1, min(n, int(round(strength))))
        seg_len = min(seg_len, n)

        start = rng.randrange(0, n - seg_len + 1)
        segment = src[start:start + seg_len]
        del src[start:start + seg_len]

        if not src:
            del routes[src_idx]
            if routes:
                src_idx = src_idx % len(routes)
            else:
                routes = [segment]
                return canonical(tuple(tuple(r) for r in routes))

        if not routes:
            routes = [segment]
            return canonical(tuple(tuple(r) for r in routes))

        # choose insertion route; allow same route if it still exists
        tgt_idx = rng.randrange(len(routes))
        if tgt_idx == src_idx and len(routes) > 1:
            tgt_idx = (tgt_idx + 1 + rng.randrange(len(routes) - 1)) % len(routes)

        tgt = routes[tgt_idx]
        pos = rng.randrange(0, len(tgt) + 1)
        new_tgt = tgt[:pos] + segment + tgt[pos:]

        if src_idx < len(routes):
            routes[src_idx] = src
            routes[tgt_idx] = new_tgt
        else:
            routes[tgt_idx] = new_tgt
            routes.append(src)

        routes = [r for r in routes if r]
        if not routes:
            return sol

        out = canonical(tuple(tuple(r) for r in routes))
        return out if out != sol else canonical(tuple(tuple(r) for r in routes + [[segment[0]]]))

        

def build_component(problem, **params):
    return RelocateContiguousSegment(problem)
