from __future__ import annotations

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


class RelatedCustomerDestruction:
    """Libera un clúster de clientes cercanos al mismo cliente semilla (Shaw-like)."""

    def __init__(self, problem, relatedness_noise: float = 0.15):
        self.problem = problem
        self.inst = problem.inst
        self.relatedness_noise = float(relatedness_noise)

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = dict(self.problem.to_assignment(sol))
        vars_all = set(assignment.keys())

        customers = list(self.inst.customers)
        n = len(customers)
        k = max(1, int(round(ratio * n)))

        seed = rng.choice(customers)

        def score(c):
            d = self.inst.dist(seed, c)
            jitter = self.relatedness_noise * rng.random()
            return d + jitter

        ordered = sorted((c for c in customers if c != seed), key=score)
        chosen = {seed}
        for c in ordered:
            if len(chosen) >= k:
                break
            chosen.add(c)

        free_vars = set()
        for c in chosen:
            for j in range(n + 1):
                if c != j:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        # If the cluster is too small due to rounding, ensure at least one arc is freed.
        free_vars &= vars_all
        if not free_vars:
            free_vars = {rng.choice(tuple(vars_all))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, relatedness_noise: float = 0.15):
    return RelatedCustomerDestruction(problem, relatedness_noise=relatedness_noise)
