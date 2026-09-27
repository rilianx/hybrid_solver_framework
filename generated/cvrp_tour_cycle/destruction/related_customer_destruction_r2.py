from __future__ import annotations

import re
from random import Random

COMPONENT = {
    "name": "related_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "relatedness_noise": {"type": "float", "range": [0.0, 1.0]},
    },
}


_ARC_RE = re.compile(r"^x_(\d+)_(\d+)$")


def _extract_customer_ids(inst):
    return list(getattr(inst, "customers", []))


def _tour_from_positive_arcs(assignment):
    succ = {}
    pred = {}
    for v, val in assignment.items():
        if val <= 0.5:
            continue
        m = _ARC_RE.match(v)
        if not m:
            continue
        i = int(m.group(1))
        j = int(m.group(2))
        if i == j:
            continue
        succ[i] = j
        pred[j] = i

    if not succ:
        return []

    starts = [i for i in succ.keys() if i not in pred]
    start = starts[0] if starts else next(iter(succ))

    tour = []
    seen = set()
    cur = start
    while cur in succ and cur not in seen:
        seen.add(cur)
        tour.append(cur)
        cur = succ[cur]
    if cur not in seen:
        tour.append(cur)
    return tour


class RelatedCustomerDestruction:
    """Libera un segmento contiguo del gran tour, centrado en un cliente semilla."""

    def __init__(self, problem, relatedness_noise: float = 0.15):
        self.problem = problem
        self.inst = problem.inst
        self.relatedness_noise = float(relatedness_noise)

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = dict(self.problem.to_assignment(sol))
        vars_all = set(assignment.keys())

        customers = _extract_customer_ids(self.inst)
        if not customers:
            return dict(assignment), set()

        n = len(customers)
        k = max(1, int(round(ratio * n)))

        tour = _tour_from_positive_arcs(assignment)
        if len(tour) < k:
            tour = customers[:]

        seed = rng.choice(tour if tour else customers)
        seed_idx = tour.index(seed) if seed in tour else rng.randrange(len(tour))

        def score(c):
            d = self.inst.dist(seed, c)
            jitter = self.relatedness_noise * rng.random()
            return d + jitter

        # Select a contiguous block in tour order, but bias its center toward related customers.
        ordered_candidates = sorted(tour, key=score)
        anchor = ordered_candidates[0] if ordered_candidates else seed
        anchor_idx = tour.index(anchor) if anchor in tour else seed_idx

        length = min(k, len(tour))
        start = max(0, min(len(tour) - length, min(seed_idx, anchor_idx) - rng.randrange(0, 2) if length > 1 else seed_idx))
        if start + length > len(tour):
            start = max(0, len(tour) - length)

        block = set(tour[start : start + length])

        free_vars = set()
        for v, val in assignment.items():
            m = _ARC_RE.match(v)
            if not m:
                continue
            i = int(m.group(1))
            j = int(m.group(2))
            if i in block or j in block:
                free_vars.add(v)

        free_vars &= vars_all
        if not free_vars:
            arc_vars = [v for v in vars_all if _ARC_RE.match(v)]
            free_vars = {rng.choice(arc_vars)} if arc_vars else {rng.choice(tuple(vars_all))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, relatedness_noise: float = 0.15):
    return RelatedCustomerDestruction(problem, relatedness_noise=relatedness_noise)
