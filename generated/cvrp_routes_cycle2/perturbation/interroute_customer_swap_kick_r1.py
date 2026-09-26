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
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.canonical(sol)
        routes = [list(route) for route in sol]
        if sum(len(r) for r in routes) <= 1:
            return sol

        steps = max(1, int(round(strength)))
        for _ in range(steps):
            nonempty = [i for i, r in enumerate(routes) if r]
            if len(nonempty) < 2:
                break

            i, j = rng.sample(nonempty, 2)
            ri, rj = routes[i], routes[j]
            pi = rng.randrange(len(ri))
            pj = rng.randrange(len(rj))
            ri[pi], rj[pj] = rj[pj], ri[pi]

        new_sol = self.canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            # Force a different swap between distinct routes if possible
            routes = [list(route) for route in sol]
            nonempty = [i for i, r in enumerate(routes) if r]
            if len(nonempty) >= 2:
                i, j = nonempty[0], nonempty[1]
                routes[i][0], routes[j][0] = routes[j][0], routes[i][0]
            else:
                route = routes[0]
                if len(route) >= 2:
                    route[0], route[1] = route[1], route[0]
            new_sol = self.canonical(tuple(tuple(r) for r in routes))
        return new_sol


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return InterrouteCustomerSwapKick(problem)
