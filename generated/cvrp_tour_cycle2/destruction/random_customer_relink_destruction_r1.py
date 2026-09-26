from random import Random
from typing import Any

COMPONENT = {
    "name": "random_customer_relink_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "problem.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RandomCustomerRelinkDestruction:
    """Libera clientes aleatorios junto con todos sus arcos incidentes."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _selected_customers(self, assignment: dict[str, float], ratio: float, rng: Random) -> set[int]:
        customers = list(self.inst.customers)
        if not customers:
            return set()
        k = max(1, int(round(ratio * len(customers))))
        k = min(k, len(customers))
        rng.shuffle(customers)
        return set(customers[:k])

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        selected = self._selected_customers(assignment, ratio, rng)

        free_vars: set[str] = set()
        for var in assignment:
            if var.startswith("x_"):
                _, i, j = var.split("_")
                ii = int(i)
                jj = int(j)
                if ii in selected or jj in selected:
                    free_vars.add(var)

        if not free_vars:
            # Fallback: free one outgoing arc from a random customer if possible.
            for c in self.inst.customers:
                for var in assignment:
                    if var == f"x_{c}_0" or var.startswith(f"x_{c}_") or var.startswith(f"x_0_{c}"):
                        free_vars.add(var)
                        break
                if free_vars:
                    break

        if not free_vars:
            # Absolute fallback: free any single structural variable.
            for var in assignment:
                if var.startswith("x_"):
                    free_vars.add(var)
                    break

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    ratio = float(params.get("ratio", 0.2))
    return RandomCustomerRelinkDestruction(problem, problem.inst)
