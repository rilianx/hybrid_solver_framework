from __future__ import annotations

from random import Random
from typing import Any

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "related_customers_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.8]}},
}


class RelatedCustomersDestruction:
    """Libera un racimo de clientes cercanos al depósito/entre sí."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _relatedness(self, a: int, b: int) -> float:
        # menor es mejor: distancia + diferencia de demanda
        return float(self.inst.dist(a, b)) + 0.1 * abs(float(self.inst.demand[a]) - float(self.inst.demand[b]))

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        sol = canonical(sol)
        assignment = self.problem.to_assignment(sol)
        n = int(self.inst.n_customers)
        customers = list(range(1, n + 1))

        seed = rng.choice(customers)
        k = max(1, min(n, int(round(ratio * n))))

        ranked = sorted(
            (self._relatedness(seed, c), c) for c in customers if c != seed
        )
        removed = {seed}
        for _, c in ranked[: max(0, k - 1)]:
            removed.add(c)

        # un poco de azar para diversificar el racimo
        if len(removed) < k:
            remaining = [c for c in customers if c not in removed]
            rng.shuffle(remaining)
            for c in remaining:
                removed.add(c)
                if len(removed) >= k:
                    break

        free_vars: set[str] = set()
        for name in assignment:
            if not name.startswith("x_"):
                continue
            _, i, j = name.split("_")
            if int(i) in removed or int(j) in removed:
                free_vars.add(name)

        if not free_vars:
            c = seed
            for name in assignment:
                if name.startswith(f"x_0_{c}") or name.startswith(f"x_{c}_0"):
                    free_vars.add(name)

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RelatedCustomersDestruction(problem, problem.inst)
