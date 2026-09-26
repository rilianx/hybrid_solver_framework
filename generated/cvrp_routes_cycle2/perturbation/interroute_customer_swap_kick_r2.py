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

        # Route-pair suffix exchange:
        # pick two distinct routes and swap their tails after two cut points.
        # This changes the route structure more broadly than a single-customer
        # relocation or swap, while preserving the customer set exactly.
        steps = max(1, int(round(strength)))
        for _ in range(steps):
            eligible = [i for i, r in enumerate(routes) if len(r) >= 1]
            if len(eligible) < 2:
                break

            i, j = rng.sample(eligible, 2)
            ri, rj = routes[i], routes[j]
            if not ri or not rj:
                continue

            # Prefer non-trivial cuts; allow empty prefixes only as fallback.
            ai = rng.randrange(0, len(ri) + 1)
            aj = rng.randrange(0, len(rj) + 1)

            prefix_i, suffix_i = ri[:ai], ri[ai:]
            prefix_j, suffix_j = rj[:aj], rj[aj:]

            # If both cuts are at the ends, this becomes a no-op; retry by
            # forcing at least one non-empty exchanged part when possible.
            if not suffix_i and not suffix_j:
                if len(ri) >= 2:
                    ai = rng.randrange(1, len(ri))
                    prefix_i, suffix_i = ri[:ai], ri[ai:]
                if len(rj) >= 2:
                    aj = rng.randrange(1, len(rj))
                    prefix_j, suffix_j = rj[:aj], rj[aj:]

            routes[i] = prefix_i + suffix_j
            routes[j] = prefix_j + suffix_i

        new_sol = self.canonical(tuple(tuple(route) for route in routes))
        if new_sol == sol:
            # Deterministic fallback: exchange non-empty suffixes between the
            # first two non-empty routes if possible.
            routes = [list(route) for route in sol]
            nonempty = [idx for idx, r in enumerate(routes) if r]
            if len(nonempty) >= 2:
                i, j = nonempty[0], nonempty[1]
                ri, rj = routes[i], routes[j]
                ai = 1 if len(ri) > 1 else 0
                aj = 1 if len(rj) > 1 else 0
                routes[i] = ri[:ai] + rj[aj:]
                routes[j] = rj[:aj] + ri[ai:]
                new_sol = self.canonical(tuple(tuple(route) for route in routes))
            elif len(nonempty) == 1 and len(routes[nonempty[0]]) >= 2:
                # Intra-route fallback: reverse a non-trivial segment.
                k = nonempty[0]
                route = routes[k]
                a, b = 0, 2
                routes[k] = route[:a] + list(reversed(route[a:b])) + route[b:]
                new_sol = self.canonical(tuple(tuple(route) for route in routes))

        return new_sol


def build_component(problem, **params):
    strength = float(params.get("strength", 3.0))
    return InterrouteCustomerSwapKick(problem, strength=strength)
