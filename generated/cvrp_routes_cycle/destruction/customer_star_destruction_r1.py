from random import Random
from typing import Any

COMPONENT = {
    "name": "customer_star_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.8]},
        "radius": {"type": "float", "range": [0.0, 1.0]},
    },
}


class CustomerStarDestruction:
    """Libera todas las aristas incidentes a un conjunto de clientes seleccionados."""

    def __init__(self, problem, ratio: float = 0.25, radius: float = 0.35):
        self.problem = problem
        self.inst = problem.inst
        self.ratio = float(ratio)
        self.radius = float(radius)

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        all_vars = set(assignment)

        customers = list(range(1, self.inst.n_customers + 1))
        if not customers:
            return {}, set()

        target_customers = max(1, int(round(float(ratio) * len(customers))))

        # Seed en un cliente aleatorio; prioriza vecinos cercanos dentro de un radio.
        seed = rng.choice(customers)
        seed_xy = (self.inst.coords[seed][0], self.inst.coords[seed][1])

        def dist_to_seed(c: int) -> float:
            x, y = self.inst.coords[c]
            dx = x - seed_xy[0]
            dy = y - seed_xy[1]
            return (dx * dx + dy * dy) ** 0.5

        ordered = sorted(customers, key=lambda c: (dist_to_seed(c), c))
        chosen_customers = [seed]
        for c in ordered:
            if c == seed:
                continue
            if len(chosen_customers) >= target_customers:
                break
            if dist_to_seed(c) <= self.radius * max(1.0, max(dist_to_seed(k) for k in ordered)):
                chosen_customers.append(c)

        if len(chosen_customers) < target_customers:
            remaining = [c for c in customers if c not in chosen_customers]
            rng.shuffle(remaining)
            chosen_customers.extend(remaining[: target_customers - len(chosen_customers)])

        free_vars = set()
        chosen_set = set(chosen_customers)

        for name in all_vars:
            # Variables de arco x_i_j
            try:
                _, i, j = name.split("_")
                i = int(i)
                j = int(j)
            except Exception:
                continue
            if i in chosen_set or j in chosen_set:
                free_vars.add(name)

        if not free_vars:
            free_vars = {rng.choice(sorted(all_vars))}

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, ratio: float = 0.25, radius: float = 0.35):
    return CustomerStarDestruction(problem, ratio=ratio, radius=radius)
