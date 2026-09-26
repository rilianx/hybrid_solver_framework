from __future__ import annotations

import math
from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "clarke_wright_savings_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "random_tie_break": {"type": "bool", "values": [False, True]},
        "merge_threshold": {"type": "float", "range": [0.0, 1.0]},
    },
}


class ClarkeWrightSavingsConstructor:
    """Constructor inspirado en Clarke-Wright.

    Idea:
    - empieza con una ruta por cliente;
    - calcula ahorros s(i,j)=d(0,i)+d(0,j)-d(i,j);
    - intenta fusionar rutas si la concatenación respeta capacidad;
    - ordena los ahorros de mayor a menor.
    """

    def __init__(self, problem: Any, random_tie_break: bool = False, merge_threshold: float = 0.0):
        self.problem = problem
        self.random_tie_break = random_tie_break
        self.merge_threshold = merge_threshold

    def _route_load(self, inst, route):
        return sum(inst.demand[c] for c in route)

    def _savings_list(self, inst, rng: Random):
        custs = list(inst.customers)
        items = []
        for i_idx, i in enumerate(custs):
            for j in custs[i_idx + 1 :]:
                s = inst.dist(0, i) + inst.dist(0, j) - inst.dist(i, j)
                tie = rng.random() if self.random_tie_break else 0.0
                items.append((s, tie, i, j))
        items.sort(key=lambda t: (t[0], t[1], -t[2], -t[3]), reverse=True)
        return items

    def _mergeable(self, r1, r2, i, j):
        return r1 and r2 and r1[-1] == i and r2[0] == j

    def _merge_routes(self, routes, i, j, inst):
        pos = {}
        for idx, r in enumerate(routes):
            if r:
                pos[r[0]] = ("start", idx)
                pos[r[-1]] = ("end", idx)
        if i not in pos or j not in pos:
            return routes
        ei, idx_i = pos[i]
        sj, idx_j = pos[j]
        if idx_i == idx_j or ei != "end" or sj != "start":
            return routes
        r1, r2 = routes[idx_i], routes[idx_j]
        if self._route_load(inst, r1) + self._route_load(inst, r2) > inst.capacity + 1e-9:
            return routes
        new_r = r1 + r2
        new_routes = [r for k, r in enumerate(routes) if k not in (idx_i, idx_j)]
        new_routes.append(new_r)
        return new_routes

    def build(self, inst, rng: Random):
        routes = [(c,) for c in inst.customers]
        savings = self._savings_list(inst, rng)
        for s, _, i, j in savings:
            if s < self.merge_threshold:
                break
            routes = self._merge_routes(routes, i, j, inst)
        sol = canonical(routes)
        if not self.problem.is_feasible(sol):
            # Repair: greedy reinsertion into routes with available slack.
            unrouted = []
            seen = set()
            for r in sol:
                for c in r:
                    if c not in seen:
                        seen.add(c)
                    else:
                        unrouted.append(c)
            missing = [c for c in inst.customers if c not in seen]
            pool = missing + unrouted
            fixed = [list(r) for r in sol]
            for c in pool:
                placed = False
                for r in fixed:
                    if self._route_load(inst, tuple(r)) + inst.demand[c] <= inst.capacity + 1e-9:
                        r.append(c)
                        placed = True
                        break
                if not placed:
                    fixed.append([c])
            sol = canonical(tuple(tuple(r) for r in fixed))
        if not self.problem.is_feasible(sol):
            sol = canonical([(c,) for c in inst.customers])
        return sol


def build_component(problem, random_tie_break: bool = False, merge_threshold: float = 0.0):
    return ClarkeWrightSavingsConstructor(
        problem,
        random_tie_break=random_tie_break,
        merge_threshold=merge_threshold,
    )
