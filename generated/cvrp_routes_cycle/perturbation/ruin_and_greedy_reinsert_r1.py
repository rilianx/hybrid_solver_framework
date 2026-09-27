from __future__ import annotations

from random import Random
from typing import List, Tuple

from generated.cvrp_routes_cycle.model.parts import canonical


COMPONENT = {
    "name": "ruin_and_greedy_reinsert",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 30.0]}
    },
}


class RuinAndGreedyReinsert:
    def __init__(self, problem):
        self.problem = problem

    def _route_cost(self, route):
        inst = self.problem.inst
        prev = 0
        total = 0.0
        for c in route:
            total += inst.dist(prev, c)
            prev = c
        total += inst.dist(prev, 0)
        return total

    def _delta_insert(self, route, customer, pos):
        inst = self.problem.inst
        a = 0 if pos == 0 else route[pos - 1]
        b = 0 if pos == len(route) else route[pos]
        return inst.dist(a, customer) + inst.dist(customer, b) - inst.dist(a, b)

    def perturb(self, sol, strength: float, rng: Random):
        sol = canonical(sol)
        inst = self.problem.inst
        customers = [c for route in sol for c in route]
        if not customers:
            return sol

        k = max(1, min(len(customers), int(round(strength))))
        removed = set(rng.sample(customers, k))

        routes = [tuple(c for c in route if c not in removed) for route in sol]
        routes = [r for r in routes if r]

        remaining = [c for c in customers if c in removed]
        rng.shuffle(remaining)

        for c in remaining:
            best = None  # (delta, route_idx, pos)
            for ridx, route in enumerate(routes):
                load = sum(inst.demand[x] for x in route)
                if load + inst.demand[c] > inst.capacity:
                    continue
                for pos in range(len(route) + 1):
                    delta = self._delta_insert(route, c, pos)
                    cand = (delta, ridx, pos)
                    if best is None or cand < best:
                        best = cand

            if best is None:
                routes.append((c,))
            else:
                _, ridx, pos = best
                route = list(routes[ridx])
                route.insert(pos, c)
                routes[ridx] = tuple(route)

        out = canonical(tuple(routes))
        if out == sol:
            # Force a change by moving one customer to a new singleton route
            first = customers[0]
            new_routes = []
            moved = False
            for route in sol:
                rr = [c for c in route if c != first]
                if rr:
                    new_routes.append(tuple(rr))
                if first in route and not moved:
                    moved = True
            new_routes.append((first,))
            out = canonical(tuple(new_routes))

        return out

        

def build_component(problem, **params):
    return RuinAndGreedyReinsert(problem)
