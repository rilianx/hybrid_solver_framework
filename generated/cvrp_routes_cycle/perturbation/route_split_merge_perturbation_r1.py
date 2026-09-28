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
        if not routes:
            return sol

        k = max(1, int(round(strength)))
        k = min(k, len(routes))

        for _ in range(k):
            if len(routes) == 1 and len(routes[0]) <= 1:
                break

            if len(routes) >= 2 and rng.random() < 0.5:
                i, j = rng.sample(range(len(routes)), 2)
                ri = routes[i]
                rj = routes[j]
                if not ri or not rj:
                    continue

                # merge two routes, then split at a random feasible-looking point
                merged = ri + rj
                if len(merged) <= 1:
                    continue

                cut = rng.randrange(1, len(merged))
                a = merged[:cut]
                b = merged[cut:]
                routes[i] = a
                routes[j] = b
            else:
                idx = rng.randrange(len(routes))
                route = routes[idx]
                if len(route) <= 1:
                    continue

                cut = rng.randrange(1, len(route))
                a = route[:cut]
                b = route[cut:]
                routes[idx] = a
                routes.append(b)

            routes = [r for r in routes if r]

        return self.parts.canonical(tuple(tuple(r) for r in routes))


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return RouteSplitMergePerturbation(problem)
