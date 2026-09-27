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


def perturb(self, sol, strength: float, rng: Random):
    canon = self.parts.canonical
    sol = canon(sol)
    routes = [list(r) for r in sol]

    customers = list(self.inst.customers)
    if not customers:
        return canon(sol)

    n_ops = max(1, int(round(strength)))
    capacity = float(self.inst.capacity)
    demand = self.inst.demand

    def route_load(route):
        return sum(float(demand[c]) for c in route)

    for _ in range(n_ops):
        if len(routes) < 2:
            # Fallback: split one route into two subroutes to create a new inter-route structure.
            if not routes:
                c = rng.choice(customers)
                routes = [[c]]
                continue
            r_idx = rng.randrange(len(routes))
            r = routes[r_idx]
            if len(r) < 2:
                continue
            cut = rng.randrange(1, len(r))
            left, right = r[:cut], r[cut:]
            if left and right:
                routes[r_idx] = left
                routes.append(right)
            continue

        i, j = rng.sample(range(len(routes)), 2)
        ri, rj = routes[i], routes[j]
        if not ri or not rj:
            continue

        # Cross-exchange route suffixes: a route-structure kick distinct from customer relocation.
        ai = rng.randrange(len(ri))
        bj = rng.randrange(len(rj))
        new_ri = ri[:ai] + rj[bj:]
        new_rj = rj[:bj] + ri[ai:]

        if route_load(new_ri) <= capacity and route_load(new_rj) <= capacity:
            routes[i] = new_ri
            routes[j] = new_rj
        else:
            # If the full suffix swap violates capacity, do a smaller cross exchange of single customers.
            ci, cj = ri[ai], rj[bj]
            ri2 = ri[:]
            rj2 = rj[:]
            ri2[ai] = cj
            rj2[bj] = ci
            if route_load(ri2) <= capacity and route_load(rj2) <= capacity:
                routes[i] = ri2
                routes[j] = rj2
            else:
                # As last resort, rotate one route internally to diversify without relocating customers.
                if len(ri) > 1:
                    k = rng.randrange(len(ri))
                    routes[i] = ri[k:] + ri[:k]
                if len(rj) > 1:
                    k = rng.randrange(len(rj))
                    routes[j] = rj[k:] + rj[:k]

    routes = [tuple(r) for r in routes if r]
    if not routes:
        c = rng.choice(customers)
        routes = [(c,)]
    return canon(tuple(routes))
