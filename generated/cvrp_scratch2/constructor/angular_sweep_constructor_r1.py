from __future__ import annotations

import math
from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "angular_sweep_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "direction": {"type": "cat", "values": ["ccw", "cw"]},
        "anchor_noise": {"type": "float", "range": [0.0, 1.0]},
    },
}


class AngularSweepConstructor:
    """Constructor por barrido angular.

    Idea:
    - ordena clientes por ángulo polar respecto al depósito;
    - recorre en un sentido o en el contrario;
    - empaqueta secuencias contiguas sin violar capacidad.
    """

    def __init__(self, problem: Any, direction: str = "ccw", anchor_noise: float = 0.0):
        self.problem = problem
        self.direction = direction
        self.anchor_noise = anchor_noise

    def _angle(self, inst, c: int) -> float:
        x0, y0 = inst.coords[0]
        x, y = inst.coords[c]
        return math.atan2(y - y0, x - x0)

    def _ordered_customers(self, inst, rng: Random):
        custs = list(inst.customers)
        if self.anchor_noise > 0:
            # Pequeño desempate determinista controlado por rng.
            jitter = {c: (rng.random() - 0.5) * self.anchor_noise for c in custs}
            custs.sort(key=lambda c: (self._angle(inst, c) + jitter[c], c))
        else:
            custs.sort(key=lambda c: (self._angle(inst, c), c))
        if self.direction == "cw":
            custs.reverse()
        return custs

    def _pack(self, inst, ordered):
        routes = []
        cur, load = [], 0.0
        for c in ordered:
            d = inst.demand[c]
            if cur and load + d > inst.capacity + 1e-9:
                routes.append(tuple(cur))
                cur, load = [], 0.0
            cur.append(c)
            load += d
        if cur:
            routes.append(tuple(cur))
        return canonical(routes)

    def build(self, inst, rng: Random):
        ordered = self._ordered_customers(inst, rng)
        sol = self._pack(inst, ordered)
        if not self.problem.is_feasible(sol):
            # Repair by a stricter first-fit pass on the same order.
            sol = canonical(self._pack(inst, ordered))
        if not self.problem.is_feasible(sol):
            sol = canonical([(c,) for c in inst.customers])
        return sol


def build_component(problem, direction: str = "ccw", anchor_noise: float = 0.0):
    return AngularSweepConstructor(problem, direction=direction, anchor_noise=anchor_noise)
