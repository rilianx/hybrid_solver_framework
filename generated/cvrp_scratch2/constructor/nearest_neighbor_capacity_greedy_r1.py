from __future__ import annotations

import math
from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "nearest_neighbor_capacity_greedy",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "start_mode": {"type": "cat", "values": ["random", "farthest", "closest_to_depot"]},
    },
}


class NearestNeighborCapacityGreedy:
    """Constructor basado en vecino más cercano con respeto estricto de capacidad.

    Idea:
    - arranca una ruta desde un cliente semilla;
    - va añadiendo el cliente factible más cercano al último cliente de la ruta;
    - cuando no caben más, cierra la ruta y abre otra.
    """

    def __init__(self, problem: Any, start_mode: str = "farthest"):
        self.problem = problem
        self.start_mode = start_mode

    def _seed_order(self, inst):
        custs = list(inst.customers)
        if self.start_mode == "random":
            return custs
        depot = 0
        if self.start_mode == "closest_to_depot":
            custs.sort(key=lambda c: inst.dist(depot, c))
        else:  # farthest
            custs.sort(key=lambda c: inst.dist(depot, c), reverse=True)
        return custs

    def _repair(self, inst, routes):
        # Rebuild from scratch if anything went wrong.
        all_customers = [c for r in routes for c in r]
        seen = set()
        uniq = []
        for c in all_customers:
            if c not in seen and 1 <= c <= inst.n_customers:
                seen.add(c)
                uniq.append(c)
        missing = [c for c in inst.customers if c not in seen]
        return self._construct(inst, uniq + missing)

    def _construct(self, inst, ordered_customers):
        unassigned = list(dict.fromkeys(ordered_customers))
        routes = []
        while unassigned:
            # Seed selection
            if self.start_mode == "random":
                seed = unassigned[0]
            else:
                if self.start_mode == "closest_to_depot":
                    seed = min(unassigned, key=lambda c: inst.dist(0, c))
                else:
                    seed = max(unassigned, key=lambda c: inst.dist(0, c))
            route = [seed]
            load = inst.demand[seed]
            unassigned.remove(seed)

            while True:
                feasible = [c for c in unassigned if load + inst.demand[c] <= inst.capacity + 1e-9]
                if not feasible:
                    break
                last = route[-1]
                nxt = min(feasible, key=lambda c: (inst.dist(last, c), inst.dist(0, c), c))
                route.append(nxt)
                load += inst.demand[nxt]
                unassigned.remove(nxt)
            routes.append(tuple(route))
        return canonical(routes)

    def build(self, inst, rng: Random):
        ordered = self._seed_order(inst)
        if self.start_mode == "random":
            rng.shuffle(ordered)
        sol = self._construct(inst, ordered)
        if not self.problem.is_feasible(sol):
            sol = self._repair(inst, sol)
        if not self.problem.is_feasible(sol):
            # Absolute fallback: one customer per route.
            sol = canonical([(c,) for c in inst.customers])
        return sol


def build_component(problem, start_mode: str = "farthest"):
    return NearestNeighborCapacityGreedy(problem, start_mode=start_mode)
