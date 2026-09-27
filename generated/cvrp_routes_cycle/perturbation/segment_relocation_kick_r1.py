from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "segment_relocation_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 20.0]}},
}


class SegmentRelocationKick:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts

    def perturb(self, sol, strength: float, rng: Random):
        canon = self.parts.canonical
        sol = canon(sol)

        routes = [list(r) for r in sol]
        if not routes:
            c = rng.choice(list(self.inst.customers))
            return canon(((c,),))

        n_moves = max(1, int(round(strength)))
        n_moves = min(n_moves, max(1, sum(len(r) for r in routes)))

        for _ in range(n_moves):
            nonempty = [idx for idx, r in enumerate(routes) if r]
            if not nonempty:
                break

            src_idx = rng.choice(nonempty)
            src = routes[src_idx]
            if len(src) == 1:
                pos = 0
                seg_len = 1
            else:
                pos = rng.randrange(len(src))
                seg_len = rng.randint(1, min(len(src) - pos, max(1, int(round(strength)))))

            segment = src[pos : pos + seg_len]
            del src[pos : pos + seg_len]
            if not src:
                routes.pop(src_idx)
                if routes:
                    src_idx = min(src_idx, len(routes) - 1)

            if routes:
                tgt_idx = rng.randrange(len(routes) + 1)
                if tgt_idx == len(routes):
                    routes.append([])
                target = routes[tgt_idx]
                insert_pos = rng.randrange(len(target) + 1)
                if rng.random() < 0.5:
                    segment = list(reversed(segment))
                target[insert_pos:insert_pos] = segment
            else:
                routes.append(list(segment))

        routes = [tuple(r) for r in routes if r]
        if not routes:
            c = rng.choice(list(self.inst.customers))
            routes = [(c,)]
        return canon(tuple(routes))


def build_component(problem, **params):
    return SegmentRelocationKick(problem)
