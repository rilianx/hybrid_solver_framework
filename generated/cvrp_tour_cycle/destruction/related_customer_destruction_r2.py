from math import hypot
from random import Random

COMPONENT = {
    "name": "related_customer_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RelatedCustomerDestruction:
    """Libera arcos asociados a un cliente semilla y a sus clientes más cercanos."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def _coords(self, c):
        # Intenta usar coordenadas estándar del CVRP; si no están, cae a la distancia.
        if hasattr(self.inst, "coords"):
            return self.inst.coords[c]
        if hasattr(self.inst, "x") and hasattr(self.inst, "y"):
            return (self.inst.x[c], self.inst.y[c])
        return None

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        customers = list(self.inst.customers)
        if not customers:
            return dict(assignment), set()

        seed = rng.choice(customers)

        def dist_to_seed(c):
            if hasattr(self.inst, "dist"):
                return float(self.inst.dist(seed, c))
            a = self._coords(seed)
            b = self._coords(c)
            if a is None or b is None:
                return 0.0
            return hypot(a[0] - b[0], a[1] - b[1])

        ordered = sorted((c for c in customers if c != seed), key=dist_to_seed)
        target_customers = {seed}

        n = len(customers)
        k = max(1, min(n, int(round(ratio * n))))
        for c in ordered:
            if len(target_customers) >= k:
                break
            target_customers.add(c)

        free_vars = set()
        for c in target_customers:
            for i in range(self.inst.n_customers + 1):
                if i != c and f"x_{i}_{c}" in assignment:
                    free_vars.add(f"x_{i}_{c}")
                if i != c and f"x_{c}_{i}" in assignment:
                    free_vars.add(f"x_{c}_{i}")

        if not free_vars:
            free_vars.add(rng.choice(list(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.2):
    return RelatedCustomerDestruction(problem, problem.inst)


def destroy(self, sol, ratio: float, rng: Random):
    assignment = self.problem.to_assignment(sol)
    customers = list(getattr(self.inst, "customers", ()))
    if not customers:
        return dict(assignment), set()

    seed = rng.choice(customers)

    def demand(c):
        for attr in ("demand", "demands", "q", "service", "load"):
            if hasattr(self.inst, attr):
                val = getattr(self.inst, attr)
                try:
                    return float(val[c])
                except Exception:
                    pass
        return 0.0

    seed_demand = demand(seed)

    def demand_distance(c):
        return abs(demand(c) - seed_demand)

    # Relatedness is based on demand similarity rather than spatial contiguity.
    ordered = sorted((c for c in customers if c != seed), key=demand_distance)

    n = len(customers)
    k = max(1, min(n, int(round(ratio * n))))
    target_customers = {seed}
    for c in ordered:
        if len(target_customers) >= k:
            break
        target_customers.add(c)

    def mentions_customer(var_name, c):
        if not isinstance(var_name, str):
            return False
        parts = var_name.split("_")
        sc = str(c)
        return sc in parts

    free_vars = set()
    for v in assignment:
        if any(mentions_customer(v, c) for c in target_customers):
            free_vars.add(v)

    if not free_vars and assignment:
        free_vars.add(rng.choice(list(assignment.keys())))

    partial = {v: val for v, val in assignment.items() if v not in free_vars}
    return partial, free_vars
