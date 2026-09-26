from random import Random

COMPONENT = {
    "name": "interroute_customer_swap_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 50.0]},
    },
}


class InterrouteCustomerSwapKick:
    def __init__(self, problem, strength: float = 3.0):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst
        self.strength = strength

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.canonical(sol)
        routes = [list(route) for route in sol]
        total_customers = sum(len(r) for r in routes)
        if total_customers <= 1:
            return sol

        # Interroute customer swap kick:
        # repeatedly swap one customer from one route with one customer from
        # another route. This changes two positions at a time and explores a
        # different neighborhood from relocation-based kicks.
        steps = max(1, int(round(strength)))
        changed = False

        for _ in range(steps):
            eligible = [i for i, r in enumerate(routes) if len(r) >= 1]
            if len(eligible) < 2:
                break

            i, j = rng.sample(eligible, 2)
            ri, rj = routes[i], routes[j]
            pi = rng.randrange(len(ri))
            pj = rng.randrange(len(rj))
            ri[pi], rj[pj] = rj[pj], ri[pi]
            changed = True

        new_sol = self.canonical(tuple(tuple(route) for route in routes))
        if new_sol == sol and changed:
            # Deterministic fallback: swap the first customers of the first two
            # non-empty routes, if possible.
            routes = [list(route) for route in sol]
            nonempty = [idx for idx, r in enumerate(routes) if r]
            if len(nonempty) >= 2:
                i, j = nonempty[0], nonempty[1]
                ri, rj = routes[i], routes[j]
                ri[0], rj[0] = rj[0], ri[0]
                new_sol = self.canonical(tuple(tuple(route) for route in routes))
            elif len(nonempty) == 1 and len(routes[nonempty[0]]) >= 2:
                # If only one route exists, swap two customers within it as a
                # minimal fallback to avoid returning the original solution.
                k = nonempty[0]
                route = routes[k]
                route[0], route[1] = route[1], route[0]
                new_sol = self.canonical(tuple(tuple(route) for route in routes))

        return new_sol


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return InterrouteCustomerSwapKick(problem, strength=strength)
