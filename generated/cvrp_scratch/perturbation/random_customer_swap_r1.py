from __future__ import annotations

from random import Random

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "random_customer_swap",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class RandomCustomerSwap:
    def perturb(self, sol, strength: float, rng: Random):
        routes = [list(r) for r in sol]
        if len(routes) == 0:
            return sol

        swaps = max(1, int(round(strength)))
        for _ in range(swaps):
            nonempty = [i for i, r in enumerate(routes) if r]
            if len(nonempty) == 0:
                break
            if len(nonempty) == 1 and len(routes[nonempty[0]]) < 2:
                break

            r1 = rng.choice(nonempty)
            c1_pos = rng.randrange(len(routes[r1]))
            c1 = routes[r1][c1_pos]

            r2 = rng.choice(nonempty)
            c2_pos = rng.randrange(len(routes[r2]))
            c2 = routes[r2][c2_pos]

            if r1 == r2 and c1_pos == c2_pos:
                if len(routes[r1]) >= 2:
                    c2_pos = (c1_pos + 1) % len(routes[r1])
                    c2 = routes[r1][c2_pos]
                else:
                    continue

            routes[r1][c1_pos], routes[r2][c2_pos] = c2, c1

        new_sol = canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            nonempty = [i for i, r in enumerate(routes) if len(r) >= 2]
            if nonempty:
                r = rng.choice(nonempty)
                i, j = rng.sample(range(len(routes[r])), 2)
                routes[r][i], routes[r][j] = routes[r][j], routes[r][i]
                new_sol = canonical(tuple(tuple(r) for r in routes))
        return new_sol


def build_component(problem, **params):
    return RandomCustomerSwap()
