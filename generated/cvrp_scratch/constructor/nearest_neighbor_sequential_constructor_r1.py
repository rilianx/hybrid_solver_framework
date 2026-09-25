from __future__ import annotations

from random import Random
from typing import Any
import math

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "nearest_neighbor_sequential_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "seed_policy": {"type": "cat", "values": ["random", "farthest_first"]},
        "lookahead": {"type": "int", "range": [0, 5]},
    },
}


class NearestNeighborSequentialConstructor:
    """Constructor secuencial: inicia una ruta y va agregando el cliente factible más cercano al último cliente."""

    def __init__(self, problem: Any, seed_policy: str = "random", lookahead: int = 0):
        self.problem = problem
        self.seed_policy = seed_policy
        self.lookahead = lookahead

    def _route_load(self, inst, route):
        return sum(inst.demand[c] for c in route)

    def _best_start(self, inst, unrouted, rng: Random):
        if self.seed_policy == "farthest_first":
            return max(unrouted, key=lambda c: inst.dist(0, c))
        return rng.choice(unrouted)

    def build(self, inst, rng: Random):
        unrouted = set(inst.customers)
        routes = []
        while unrouted:
            start = self._best_start(inst, list(unrouted), rng)
            route = [start]
            unrouted.remove(start)
            load = inst.demand[start]

            while unrouted:
                last = route[-1]
                candidates = [c for c in unrouted if load + inst.demand[c] <= inst.capacity + 1e-9]
                if not candidates:
                    break

                def score(c):
                    d1 = inst.dist(last, c)
                    if self.lookahead <= 0:
                        return d1
                    future = min((inst.dist(c, d2) for d2 in unrouted if d2 != c), default=0.0)
                    return d1 + 0.25 * future

                nxt = min(candidates, key=lambda c: (score(c), c))
                route.append(nxt)
                unrouted.remove(nxt)
                load += inst.demand[nxt]

            routes.append(tuple(route))

        sol = canonical(routes)
        if hasattr(self.problem, "is_feasible") and not self.problem.is_feasible(sol):
            # Reparación conservadora: reconstrucción por inserción secuencial greedy.
            unrouted = list(inst.customers)
            routes = []
            while unrouted:
                c0 = max(unrouted, key=lambda c: inst.dist(0, c))
                route = [c0]
                unrouted.remove(c0)
                load = inst.demand[c0]
                changed = True
                while changed:
                    changed = False
                    best = None
                    best_key = None
                    for c in unrouted:
                        if load + inst.demand[c] > inst.capacity + 1e-9:
                            continue
                        key = (inst.dist(route[-1], c), c)
                        if best is None or key < best_key:
                            best, best_key = c, key
                    if best is not None:
                        route.append(best)
                        unrouted.remove(best)
                        load += inst.demand[best]
                        changed = True
                routes.append(tuple(route))
            sol = canonical(routes)
        return sol


def build_component(problem, seed_policy: str = "random", lookahead: int = 0):
    return NearestNeighborSequentialConstructor(problem, seed_policy=seed_policy, lookahead=lookahead)
