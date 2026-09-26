from random import Random

COMPONENT = {
    "name": "customer_relocation_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class CustomerRelocationPerturbation:
    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.parts.canonical(sol)
        routes = [list(r) for r in sol]
        customers = [c for route in routes for c in route]
        if len(customers) <= 1:
            return sol

        k = max(1, min(len(customers), int(round(strength))))
        picked = rng.sample(customers, k)

        remaining = []
        picked_set = set(picked)
        for route in routes:
            new_route = [c for c in route if c not in picked_set]
            if new_route:
                remaining.append(new_route)

        for c in picked:
            if not remaining or rng.random() < 0.5:
                remaining.append([c])
                continue

            idx = rng.randrange(len(remaining))
            route = remaining[idx]
            pos = rng.randrange(len(route) + 1)
            route.insert(pos, c)
            remaining[idx] = route

        return self.parts.canonical(tuple(tuple(r) for r in remaining))


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return CustomerRelocationPerturbation(problem)
