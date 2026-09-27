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

        # Build a relatedness ranking around the seed using the instance distance.
        def score(c):
            d = self.inst.dist(seed, c)
            jitter = self.relatedness_noise * rng.random()
            return (d + jitter, c)

        ranked = sorted(tour, key=score) if tour else [seed]
        anchor = ranked[0]
        anchor_idx = tour.index(anchor) if anchor in tour else seed_idx

        # Create a contiguous block in the tour, but center it on a pair
        # seed/anchor that are close in distance space, not randomly selected.
        length = min(k, len(tour))
        left = min(seed_idx, anchor_idx)
        right = max(seed_idx, anchor_idx)
        if length == 1:
            start = seed_idx
        else:
            desired_center = (left + right) // 2
            start = max(0, min(len(tour) - length, desired_center - length // 2))
        block = set(tour[start : start + length])

        free_vars = set()
        # In grande-tour models, freeing the variables tied to the selected customers
        # produces a structurally different neighborhood than freeing random customer sets:
        # here we release a contiguous tour segment.
        for v, val in assignment.items():
            if val <= 0.5:
                continue
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
            if arc_vars:
                # Ensure at least one customer-related structural variable is freed.
                free_vars = {rng.choice(arc_vars)}
            elif vars_all:
                free_vars = {rng.choice(tuple(vars_all))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, relatedness_noise: float = 0.15):
    return RelatedCustomerDestruction(problem, relatedness_noise=relatedness_noise)


def _is_tour_position_var(var_name: str) -> bool:
    # Positional/order variables in grande-tour formulations often use a customer id
    # in their name; we keep this conservative and only use it when it clearly
    # matches a customer index token.
    return bool(_ARC_RE.match(var_name))
