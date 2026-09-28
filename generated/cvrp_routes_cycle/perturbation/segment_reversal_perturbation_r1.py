from random import Random

COMPONENT = {
    "name": "segment_reversal_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class SegmentReversalPerturbation:
    def __init__(self, problem):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts

    def perturb(self, sol, strength: float, rng: Random):
        sol = self.parts.canonical(sol)
        routes = [list(r) for r in sol]
        nontrivial = [i for i, r in enumerate(routes) if len(r) >= 2]

        if not routes:
            return sol

        k = max(1, int(round(strength)))
        k = min(k, max(1, len(routes)))

        changed = False
        for _ in range(k):
            if nontrivial:
                idx = rng.choice(nontrivial)
                route = routes[idx]
                if len(route) >= 2:
                    a = rng.randrange(0, len(route) - 1)
                    b = rng.randrange(a + 1, len(route))
                    segment = route[a : b + 1]
                    if len(segment) >= 2:
                        route[a : b + 1] = reversed(segment)
                        routes[idx] = route
                        changed = True
            else:
                # Fallback: move one customer to a neighboring route to ensure change
                all_customers = [(ri, ci) for ri, r in enumerate(routes) for ci in range(len(r))]
                if len(all_customers) <= 1:
                    break
                ri, ci = rng.choice(all_customers)
                c = routes[ri].pop(ci)
                if not routes[ri]:
                    routes.pop(ri)
                if not routes:
                    routes.append([c])
                else:
                    j = rng.randrange(len(routes))
                    pos = rng.randrange(len(routes[j]) + 1)
                    routes[j].insert(pos, c)
                changed = True

            nontrivial = [i for i, r in enumerate(routes) if len(r) >= 2]

        if not changed:
            # guaranteed distinctness for strength >= 1
            if len(routes) >= 1 and len(routes[0]) >= 2:
                routes[0][0], routes[0][1] = routes[0][1], routes[0][0]
            elif len(routes) >= 2:
                routes[0].append(routes[1].pop(0))
                if not routes[1]:
                    routes.pop(1)

        routes = [r for r in routes if r]
        return self.parts.canonical(tuple(tuple(r) for r in routes))


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return SegmentReversalPerturbation(problem)
