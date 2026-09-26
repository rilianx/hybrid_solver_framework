from __future__ import annotations

from random import Random
from typing import List, Tuple

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "random_customer_relocate",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class RandomCustomerRelocate:
    def perturb(self, sol, strength: float, rng: Random):
        routes = [list(r) for r in sol]
        if not routes:
            return sol

        moves = max(1, int(round(strength)))
        for _ in range(moves):
            nonempty = [ri for ri, r in enumerate(routes) if r]
            if not nonempty:
                break
            src = rng.choice(nonempty)
            route = routes[src]
            pos = rng.randrange(len(route))
            cust = route.pop(pos)
            if not route:
                routes.pop(src)
                if not routes:
                    routes = [[cust]]
                    continue
                if src < len(routes):
                    pass
            dst = rng.randrange(len(routes) + 1)
            ins = rng.randrange(len(routes[dst]) + 1) if dst < len(routes) else 0
            if dst == len(routes):
                routes.append([cust])
            else:
                routes[dst].insert(ins, cust)

        new_sol = canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            routes = [list(r) for r in sol]
            src = rng.randrange(len(routes))
            if len(routes[src]) >= 1:
                pos = rng.randrange(len(routes[src]))
                cust = routes[src].pop(pos)
                dst = (src + 1) % len(routes) if len(routes) > 1 else 0
                routes[dst].append(cust)
            new_sol = canonical(tuple(tuple(r) for r in routes))
        return new_sol


def build_component(problem, **params):
    return RandomCustomerRelocate()
