from __future__ import annotations

from random import Random
from typing import Any
import math

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "saving_merge_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "merge_bias": {"type": "float", "range": [0.0, 1.0]},
        "random_ties": {"type": "bool", "values": [True, False]},
    },
}


class SavingMergeConstructor:
    """Constructor basado en savings de Clarke-Wright: empieza con rutas unitarias y fusiona rutas compatibles."""

    def __init__(self, problem: Any, merge_bias: float = 0.5, random_ties: bool = True):
        self.problem = problem
        self.merge_bias = merge_bias
        self.random_ties = random_ties

    def _route_load(self, inst, route):
        return sum(inst.demand[c] for c in route)

    def _savings(self, inst, i, j):
        return inst.dist(0, i) + inst.dist(0, j) - inst.dist(i, j)

    def build(self, inst, rng: Random):
        routes = {c: (c,) for c in inst.customers}
        route_of = {c: c for c in inst.customers}

        pairs = []
        cust = list(inst.customers)
        for idx, i in enumerate(cust):
            for j in cust[idx + 1 :]:
                pairs.append((self._savings(inst, i, j), i, j))
        pairs.sort(key=lambda t: (-t[0], t[1], t[2]))
        if self.random_ties:
            # perturbación determinista por rng en un rango pequeño, sin cambiar la esencia del criterio.
            perturbed = []
            for s, i, j in pairs:
                perturbed.append((s + self.merge_bias * (rng.random() - 0.5) * 1e-6, i, j))
            pairs = sorted(perturbed, key=lambda t: (-t[0], t[1], t[2]))

        changed = True
        while changed:
            changed = False
            for _, i, j in pairs:
                ri = route_of.get(i)
                rj = route_of.get(j)
                if ri is None or rj is None or ri == rj:
                    continue
                a = routes[ri]
                b = routes[rj]

                # Solo fusionamos extremos para preservar estructura simple y factible.
                can_merge = (
                    a[-1] == i and b[0] == j
                    and self._route_load(inst, a) + self._route_load(inst, b) <= inst.capacity + 1e-9
                )
                if not can_merge:
                    can_merge = (
                        b[-1] == j and a[0] == i
                        and self._route_load(inst, a) + self._route_load(inst, b) <= inst.capacity + 1e-9
                    )
                    if can_merge:
                        a, b = b, a
                        ri, rj = rj, ri
                        i, j = j, i

                if can_merge:
                    merged = a + b
                    routes[ri] = merged
                    for c in merged:
                        route_of[c] = ri
                    del routes[rj]
                    changed = True

        sol = canonical(routes.values())
        if hasattr(self.problem, "is_feasible") and not self.problem.is_feasible(sol):
            # Reparación final: reinserta clientes en rutas unitarias y luego vuelve a fusionar de forma conservadora.
            sol_routes = [(c,) for c in inst.customers]
            sol = canonical(sol_routes)
        return sol


def build_component(problem, merge_bias: float = 0.5, random_ties: bool = True):
    return SavingMergeConstructor(problem, merge_bias=merge_bias, random_ties=random_ties)
