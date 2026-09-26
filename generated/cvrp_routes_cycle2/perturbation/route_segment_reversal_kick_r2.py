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
    def __init__(self, problem, strength: float = 3.0):
        self.problem = problem
        self.canonical = problem.parts.canonical
        self.inst = problem.inst
        self.strength = float(strength)

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.canonical(sol)
        routes = [list(route) for route in sol]
        if not routes:
            return sol

        n_steps = max(1, int(round(strength)))
        changed = False

        for _ in range(n_steps):
            candidates = [i for i, r in enumerate(routes) if len(r) >= 2]
            if not candidates:
                break

            idx = rng.choice(candidates)
            route = routes[idx]
            m = len(route)

            # Prefer longer contiguous reversals to create a stronger kick
            max_len = m
            min_len = 2
            seg_len = min(
                max_len,
                max(min_len, int(round(2 + rng.random() * max(1, min(m - 1, int(self.strength)))))),
            )
            seg_len = min(seg_len, m)

            if seg_len == m:
                start = 0
            else:
                start = rng.randrange(0, m - seg_len + 1)
            end = start + seg_len - 1

            segment = route[start : end + 1]
            if len(segment) >= 2:
                route[start : end + 1] = reversed(segment)
                changed = True

        new_sol = self.canonical(tuple(tuple(r) for r in routes))

        if new_sol == sol:
            # Deterministic non-relocation fallback: reverse the longest feasible route prefix
            routes = [list(route) for route in sol]
            candidates = [i for i, r in enumerate(routes) if len(r) >= 2]
            if candidates:
                idx = max(candidates, key=lambda i: len(routes[i]))
                route = routes[idx]
                if len(route) == 2:
                    route.reverse()
                    changed = True
                else:
                    k = min(len(route), 3)
                    route[:k] = reversed(route[:k])
                    changed = True
            new_sol = self.canonical(tuple(tuple(r) for r in routes))

        return new_sol if changed or new_sol != sol else sol


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return RouteSegmentReversalKick(problem, strength=strength)
