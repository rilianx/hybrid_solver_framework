from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "contiguous_route_segment_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "segment_ratio": {"type": "float", "range": [0.05, 0.8]},
    },
}


class ContiguousRouteSegmentDestruction:
    """Libera un segmento contiguo del gran tour, junto con los arcos que lo conectan al resto."""

    def __init__(self, problem, segment_ratio: float = 0.25):
        self.problem = problem
        self.inst = problem.inst
        self.segment_ratio = float(segment_ratio)

    def _tour_from_assignment(self, assignment):
        succ = {}
        starts = []
        for name, val in assignment.items():
            if val <= 0.5 or not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            i = int(i)
            j = int(j)
            succ[i] = j
            if i == 0 and j != 0:
                starts.append(j)

        tour = []
        cur = starts[0] if starts else None
        seen = set()
        while cur is not None and cur not in seen and cur != 0:
            seen.add(cur)
            tour.append(cur)
            cur = succ.get(cur, 0)
        return tour

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = dict(self.problem.to_assignment(sol))
        vars_all = set(assignment.keys())
        tour = self._tour_from_assignment(assignment)
        n = len(tour)

        if n == 0:
            free_vars = {rng.choice(tuple(vars_all))}
            partial = {v: val for v, val in assignment.items() if v not in free_vars}
            return partial, free_vars

        seg_len = max(1, int(round(max(ratio, self.segment_ratio) * n)))
        seg_len = min(n, seg_len)
        start = rng.randrange(0, n)
        seg = [tour[(start + t) % n] for t in range(seg_len)]

        free_vars = set()
        chosen = set(seg)
        for c in chosen:
            for j in range(n + 1):
                if c != j:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        # Also free depot connectors of the boundary customers in the segment.
        for c in (seg[0], seg[-1]):
            free_vars.add(f"x_0_{c}")
            free_vars.add(f"x_{c}_0")

        free_vars &= vars_all
        if not free_vars:
            free_vars = {rng.choice(tuple(vars_all))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, segment_ratio: float = 0.25):
    return ContiguousRouteSegmentDestruction(problem, segment_ratio=segment_ratio)
