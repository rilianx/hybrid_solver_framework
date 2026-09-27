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
        cap = self.inst.capacity

        if not routes:
            c = rng.choice(customers)
            return canon(((c,),))

        def load(route):
            return sum(self.inst.demand[c] for c in route)

        def split_route(route):
            if len(route) < 2:
                return [route[:]]
            cuts = max(1, min(len(route) - 1, int(round(strength / 4.0)) + 1))
            idxs = sorted(rng.sample(range(1, len(route)), cuts))
            frags = []
            start = 0
            for cut in idxs + [len(route)]:
                frag = route[start:cut]
                if frag:
                    frags.append(frag)
                start = cut
            return frags if frags else [route[:]]

        n_ops = max(1, int(round(strength)))

        for _ in range(n_ops):
            if not routes:
                break

            if len(routes) == 1:
                idx = 0
                route = routes[idx]
                if len(route) >= 2:
                    frags = split_route(route)
                    if len(frags) >= 2:
                        routes.pop(idx)
                        for frag in frags:
                            routes.append(frag)
                continue

            # Distinct move: choose two routes, fragment one or both, then re-pack the pieces
            i, j = rng.sample(range(len(routes)), 2)
            if i > j:
                i, j = j, i
            ri = routes[i]
            rj = routes[j]

            pool = ri[:] + rj[:]
            if len(pool) < 2:
                continue

            # Remove the two routes and repack their customers into 2..m routes with random chunking.
            routes.pop(j)
            routes.pop(i)

            # Preserve a route-splitting flavor: create random fragments from the pooled sequence.
            if rng.random() < 0.5:
                rng.shuffle(pool)
            else:
                # Interleave prefix/suffix tendencies by taking a random split point and concatenating pieces.
                if len(pool) >= 4:
                    cut = rng.randrange(1, len(pool))
                    pool = pool[cut:] + pool[:cut]

            frags = []
            start = 0
            while start < len(pool):
                remaining = len(pool) - start
                max_take = min(remaining, max(1, int(round(strength)) + 1))
                take = rng.randint(1, max_take)
                frag = pool[start:start + take]
                frags.append(frag)
                start += take

            # Repack fragments into feasible routes; if a fragment is too large, split it further.
            packed = []
            for frag in frags:
                current = []
                current_load = 0
                for c in frag:
                    d = self.inst.demand[c]
                    if current and current_load + d > cap:
                        packed.append(current)
                        current = [c]
                        current_load = d
                    else:
                        current.append(c)
                        current_load += d
                if current:
                    packed.append(current)

            # Optionally merge some consecutive packed routes when feasible to vary route count.
            merged = []
            k = 0
            while k < len(packed):
                if k + 1 < len(packed):
                    a, b = packed[k], packed[k + 1]
                    if load(a) + load(b) <= cap and rng.random() < 0.5:
                        merged.append(a + b if rng.random() < 0.5 else b + a)
                        k += 2
                        continue
                merged.append(packed[k])
                k += 1

            routes.extend(merged)

        routes = [tuple(r) for r in routes if r]
        if not routes:
            c = rng.choice(customers)
            routes = [(c,)]
        return canon(tuple(routes))


def build_component(problem, **params):
    return RouteSplitMergeKick(problem)
