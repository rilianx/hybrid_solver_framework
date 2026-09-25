from __future__ import annotations

from random import Random
from typing import Any
import math

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "sweep_capacity_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "angle_shift": {"type": "float", "range": [0.0, 6.283185307179586]},
        "direction": {"type": "cat", "values": ["ccw", "cw"]},
    },
}


class SweepCapacityConstructor:
    """Constructor tipo sweep: ordena por ángulo polar y abre rutas factibles acumulando clientes contiguos."""

    def __init__(self, problem: Any, angle_shift: float = 0.0, direction: str = "ccw"):
        self.problem = problem
        self.angle_shift = angle_shift
        self.direction = direction

    def _angle(self, inst, c):
        x, y = inst.coords[c]
        dx = x - inst.coords[0][0]
        dy = y - inst.coords[0][1]
        a = math.atan2(dy, dx) - self.angle_shift
        if a < 0:
            a += 2 * math.pi
        return a

    def build(self, inst, rng: Random):
        customers = list(inst.customers)
        if self.direction == "cw":
            customers.sort(key=lambda c: (-self._angle(inst, c), c))
        else:
            customers.sort(key=lambda c: (self._angle(inst, c), c))

        routes = []
        i = 0
        n = len(customers)
        while i < n:
            route = []
            load = 0.0
            start_i = i
            while i < n and load + inst.demand[customers[i]] <= inst.capacity + 1e-9:
                route.append(customers[i])
                load += inst.demand[customers[i]]
                i += 1

            if not route:
                route = [customers[i]]
                i += 1

            # Pequeña mejora local: si el siguiente cliente queda muy cerca del último y cabe, lo absorbemos.
            while i < n:
                c = customers[i]
                if load + inst.demand[c] > inst.capacity + 1e-9:
                    break
                last = route[-1]
                if inst.dist(last, c) <= inst.dist(0, c) + 1e-9:
                    route.append(c)
                    load += inst.demand[c]
                    i += 1
                else:
                    break

            routes.append(tuple(route))

        sol = canonical(routes)
        if hasattr(self.problem, "is_feasible") and not self.problem.is_feasible(sol):
            # Reparación robusta: redistribuye en el orden angular original.
            routes = []
            cur = []
            load = 0.0
            for c in customers:
                d = inst.demand[c]
                if cur and load + d > inst.capacity + 1e-9:
                    routes.append(tuple(cur))
                    cur = []
                    load = 0.0
                cur.append(c)
                load += d
            if cur:
                routes.append(tuple(cur))
            sol = canonical(routes)
        return sol


def build_component(problem, angle_shift: float = 0.0, direction: str = "ccw"):
    return SweepCapacityConstructor(problem, angle_shift=angle_shift, direction=direction)
