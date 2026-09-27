from random import Random

COMPONENT = {
    "name": "contiguous_route_segment_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.from_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class ContiguousRouteSegmentDestruction:
    """Libera un bloque contiguo de arcos inducido por un segmento del gran tour."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        tour = tuple(int(c) for c in sol)
        n = len(tour)

        if n == 0:
            free_vars = set()
            partial = dict(assignment)
            return partial, free_vars

        segment_len = max(1, min(n, int(round(ratio * n))))

        start = rng.randrange(n)
        idxs = [(start + t) % n for t in range(segment_len)]
        customers = {tour[i] for i in idxs}

        free_vars = set()
        for i in customers:
            for j in range(self.inst.n_customers + 1):
                if i != j and f"x_{i}_{j}" in assignment:
                    free_vars.add(f"x_{i}_{j}")
                if i != j and f"x_{j}_{i}" in assignment:
                    free_vars.add(f"x_{j}_{i}")
        for c in customers:
            if f"x_0_{c}" in assignment:
                free_vars.add(f"x_0_{c}")
            if f"x_{c}_0" in assignment:
                free_vars.add(f"x_{c}_0")

        # Ensure at least one variable is freed even for tiny instances.
        if not free_vars:
            free_vars.add(rng.choice(list(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return ContiguousRouteSegmentDestruction(problem, problem.inst)
