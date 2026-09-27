from __future__ import annotations

from random import Random
from typing import Any

COMPONENT = {
    "name": "route_split_merge_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 25.0]}},
}


class RouteSplitMergeKick:
    def __init__(self, problem: Any):
        self.problem = problem
        self.inst = problem.inst
        self.parts = problem.parts

    def perturb(self, sol, strength: float, rng: Random):
        canon = self.parts.canonical
        sol = canon(sol)
        routes = [list(r) for r in sol]
        customers = list(self.inst.customers)

        if not routes:
            c = rng.choice(customers)
            return canon(((c,),))

        n_ops = max(1, int(round(strength)))

        for _ in range(n_ops):
            if not routes:
                break

            # With some probability, split a route into two.
            if len(routes) == 1 or rng.random() < 0.6:
                idx = rng.randrange(len(routes))
                route = routes[idx]
                if len(route) >= 2:
                    cut = rng.randrange(1, len(route))
                    left = route[:cut]
                    right = route[cut:]
                    routes[idx] = left
                    routes.append(right)
                else:
                    # singleton route: merge its customer into another route if possible
                    c = route[0]
                    if len(routes) >= 2:
                        other_idx = rng.randrange(len(routes) - 1)
                        if other_idx >= idx:
                            other_idx += 1
                        other = routes[other_idx]
                        ins = rng.randrange(len(other) + 1)
                        other[ins:ins] = [c]
                        routes.pop(idx)
                    else:
                        # create a second route by relocating another customer from same route impossible
                        continue
            else:
                # Merge two routes if capacity allows; otherwise do a controlled redistribution.
                i, j = rng.sample(range(len(routes)), 2)
                if i > j:
                    i, j = j, i
                ri, rj = routes[i], routes[j]
                load = sum(self.inst.demand[c] for c in ri) + sum(self.inst.demand[c] for c in rj)
                if load <= self.inst.capacity:
                    if rng.random() < 0.5:
                        merged = ri + rj
                    else:
                        merged = rj + ri
                    routes[i] = merged
                    routes.pop(j)
                else:
                    # Move one customer from rj into ri if feasible, else swap one element.
                    if rj:
                        c = rng.choice(rj)
                        if sum(self.inst.demand[x] for x in ri) + self.inst.demand[c] <= self.inst.capacity:
                            rj.remove(c)
                            ins = rng.randrange(len(ri) + 1)
                            ri[ins:ins] = [c]
                            if not rj:
                                routes.pop(j)
                        elif ri:
                            a = rng.randrange(len(ri))
                            b = rng.randrange(len(rj))
                            ri[a], rj[b] = rj[b], ri[a]

        routes = [tuple(r) for r in routes if r]
        if not routes:
            c = rng.choice(customers)
            routes = [(c,)]
        return canon(tuple(routes))


def build_component(problem, **params):
    return RouteSplitMergeKick(problem)
