from random import Random

COMPONENT = {
    "name": "route_split_merge_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class RouteSplitMergePerturbation:
    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.parts.canonical(sol)
        routes = [list(r) for r in sol]
        n_routes = len(routes)
        if n_routes == 0:
            return sol

        k = max(1, int(round(strength)))
        k = min(k, max(1, n_routes))

        for _ in range(k):
            if len(routes) < 2:
                break

            i, j = rng.sample(range(len(routes)), 2)
            if i > j:
                i, j = j, i

            ri = routes[i]
            rj = routes[j]
            if not ri or not rj:
                continue

            # Route-level split/merge: recombine two complete routes by swapping
            # whole contiguous blocks, instead of moving individual customers.
            # This changes the route decomposition substantially and reaches
            # neighborhoods not covered by customer relocation.
            ai = rng.randrange(1, len(ri) + 1)
            bj = rng.randrange(1, len(rj) + 1)

            # Two-way recombination of route blocks.
            new_i = ri[:ai] + rj[bj:]
            new_j = rj[:bj] + ri[ai:]

            routes[i] = new_i
            routes[j] = new_j

            routes = [r for r in routes if r]

        return self.parts.canonical(tuple(tuple(r) for r in routes))


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return RouteSplitMergePerturbation(problem)
