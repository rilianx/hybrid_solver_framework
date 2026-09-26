from random import Random

COMPONENT = {
    "name": "route_segment_reversal_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 50.0]},
    },
}


class RouteSegmentReversalKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.canonical(sol)
        routes = [list(route) for route in sol]
        if not routes:
            return sol

        steps = max(1, int(round(strength)))
        changed = False

        for _ in range(steps):
            candidates = [i for i, r in enumerate(routes) if len(r) >= 2]
            if not candidates:
                break
            idx = rng.choice(candidates)
            route = routes[idx]
            a = rng.randrange(len(route))
            b = rng.randrange(len(route))
            if a == b:
                continue
            if a > b:
                a, b = b, a
            route[a : b + 1] = reversed(route[a : b + 1])
            changed = True

        new_sol = self.canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            # Guaranteed alternative: reverse the longest route prefix if possible
            routes = [list(route) for route in sol]
            candidates = [i for i, r in enumerate(routes) if len(r) >= 2]
            if candidates:
                idx = max(candidates, key=lambda i: len(routes[i]))
                route = routes[idx]
                route[:2] = reversed(route[:2])
                changed = True
            elif routes and len(routes[0]) == 1:
                # No route segment can be reversed; fall back to moving one customer
                if len(routes) >= 2:
                    c = routes[0].pop(0)
                    routes[1].insert(0, c)
                    changed = True
            new_sol = self.canonical(tuple(tuple(r) for r in routes))

        return new_sol if changed or new_sol != sol else sol


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return RouteSegmentReversalKick(problem)
