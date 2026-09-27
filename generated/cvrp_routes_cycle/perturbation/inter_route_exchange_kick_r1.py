from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "inter_route_exchange_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 30.0]}},
}


class InterRouteExchangeKick:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts

    def perturb(self, sol, strength: float, rng: Random):
        canon = self.parts.canonical
        sol = canon(sol)
        routes = [list(r) for r in sol]

        customers = list(self.inst.customers)
        if not customers:
            return canon(sol)

        n_ops = max(1, int(round(strength)))

        def route_load(route):
            return sum(float(self.inst.demand[c]) for c in route)

        for _ in range(n_ops):
            # Prefer exchanging customers between two distinct routes.
            if len(routes) >= 2:
                i, j = rng.sample(range(len(routes)), 2)
                ri, rj = routes[i], routes[j]
                if not ri or not rj:
                    continue

                a = rng.randrange(len(ri))
                b = rng.randrange(len(rj))
                ci, cj = ri[a], rj[b]

                # Capacity-aware swap if possible; otherwise move one customer.
                load_i = route_load(ri) - float(self.inst.demand[ci]) + float(self.inst.demand[cj])
                load_j = route_load(rj) - float(self.inst.demand[cj]) + float(self.inst.demand[ci])

                if load_i <= self.inst.capacity and load_j <= self.inst.capacity:
                    ri[a], rj[b] = cj, ci
                else:
                    # Move the more disruptive one to a random route / new route.
                    if rng.random() < 0.5:
                        del ri[a]
                        if not ri:
                            routes.pop(i)
                            if j > i:
                                j -= 1
                        if routes:
                            tgt = routes[rng.randrange(len(routes))]
                            ins = rng.randrange(len(tgt) + 1)
                            tgt[ins:ins] = [ci]
                        else:
                            routes.append([ci])
                    else:
                        del rj[b]
                        if not rj:
                            routes.pop(j)
                        if routes:
                            tgt = routes[rng.randrange(len(routes))]
                            ins = rng.randrange(len(tgt) + 1)
                            tgt[ins:ins] = [cj]
                        else:
                            routes.append([cj])
            else:
                # Single-route fallback: relocate one customer to a singleton route or merge back.
                if routes and len(routes[0]) >= 2:
                    r = routes[0]
                    idx = rng.randrange(len(r))
                    c = r.pop(idx)
                    routes.append([c])
                else:
                    break

        routes = [tuple(r) for r in routes if r]
        if not routes:
            c = rng.choice(customers)
            routes = [(c,)]
        return canon(tuple(routes))


def build_component(problem, **params):
    return InterRouteExchangeKick(problem)
