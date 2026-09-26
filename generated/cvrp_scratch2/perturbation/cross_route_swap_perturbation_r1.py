from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "cross_route_swap_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class CrossRouteSwapPerturbation:
    def __init__(self, problem: Any):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        routes = [list(r) for r in sol]
        if len(routes) < 2:
            # si solo hay una ruta, intenta intercambiar dos clientes dentro de ella
            if len(routes) == 1 and len(routes[0]) >= 2:
                i, j = rng.sample(range(len(routes[0])), 2)
                routes[0][i], routes[0][j] = routes[0][j], routes[0][i]
                out = canonical(tuple(tuple(r) for r in routes))
                return out if out != sol else canonical((tuple(reversed(routes[0])),))
            return sol

        steps = max(1, min(5, int(round(strength))))
        for _ in range(steps):
            # elegir dos rutas distintas y clientes "compatibles" por cercanía geométrica
            r1, r2 = rng.sample(range(len(routes)), 2)
            if not routes[r1] or not routes[r2]:
                continue

            c1 = rng.choice(routes[r1])
            x1, y1 = inst.coords[c1]

            # vecino más cercano en la otra ruta
            c2 = min(routes[r2], key=lambda c: inst.dist(c1, c) + 0.05 * rng.random())

            # comprobar si el swap puede empeorar mucho la factibilidad; se acepta igual, pero preferimos intercambio factible
            load1 = sum(inst.demand[c] for c in routes[r1]) - inst.demand[c1] + inst.demand[c2]
            load2 = sum(inst.demand[c] for c in routes[r2]) - inst.demand[c2] + inst.demand[c1]

            routes[r1][routes[r1].index(c1)] = c2
            routes[r2][routes[r2].index(c2)] = c1

            # si quedó claramente mal y hay alternativa, sigue perturbando en otra iteración
            if load1 <= inst.capacity and load2 <= inst.capacity and rng.random() < 0.7:
                break

        new_sol = canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            # forzar cambio: intercambiar primeros clientes de dos rutas
            r1, r2 = 0, 1
            if routes[r1] and routes[r2]:
                routes[r1][0], routes[r2][0] = routes[r2][0], routes[r1][0]
                new_sol = canonical(tuple(tuple(r) for r in routes))
        return new_sol


def build_component(problem, **params):
    strength = params.get("strength", 3.0)
    return CrossRouteSwapPerturbation(problem)
