from __future__ import annotations

from random import Random

COMPONENT = {
    "name": "random_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {
        "min_block": {"type": "int", "range": [1, 10]},
    },
}


class RandomCustomerDestruction:
    """Libera clientes al azar, liberando todos los arcos incidentes a cada cliente elegido."""

    def __init__(self, problem, min_block: int = 1):
        self.problem = problem
        self.inst = problem.inst
        self.min_block = int(min_block)

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = dict(self.problem.to_assignment(sol))
        vars_all = set(assignment.keys())

        n = self.inst.n_customers
        customers = list(self.inst.customers)
        k = max(self.min_block, int(round(ratio * n)))
        k = max(1, min(n, k))

        chosen = set(rng.sample(customers, k)) if k < n else set(customers)

        free_vars = {
            v for v in vars_all
            if any(v == f"x_{i}_{j}" for i in chosen for j in range(n + 1) if i != j)
            or any(v == f"x_{i}_{j}" for j in chosen for i in range(n + 1) if i != j)
        }

        if not free_vars:
            free_vars = {rng.choice(tuple(vars_all))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, min_block: int = 1):
    return RandomCustomerDestruction(problem, min_block=min_block)
