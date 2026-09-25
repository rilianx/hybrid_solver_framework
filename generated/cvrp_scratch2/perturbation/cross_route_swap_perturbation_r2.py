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
        if not routes:
            return sol

        # Pequeño kick por intercambio de clientes, privilegiando rutas distintas.
        steps = max(1, min(5, int(round(strength))))
        original = sol

        for _ in range(steps):
            if len(routes) >= 2:
                # Intentar intercambio entre dos rutas distintas.
                r1, r2 = rng.sample(range(len(routes)), 2)
                if not routes[r1] or not routes[r2]:
                    continue

                c1 = rng.choice(routes[r1])
                c2 = rng.choice(routes[r2])

                if c1 == c2:
                    continue

                i1 = routes[r1].index(c1)
                i2 = routes[r2].index(c2)
                routes[r1][i1], routes[r2][i2] = c2, c1

                new_sol = canonical(tuple(tuple(r) for r in routes))
                if new_sol != original:
                    return new_sol

                # deshacer exacto si no cambió
                routes[r1][i1], routes[r2][i2] = c1, c2
            else:
                # Una sola ruta: intercambio interno garantizado.
                route = routes[0]
                if len(route) < 2:
                    return sol
                i, j = rng.sample(range(len(route)), 2)
                if i == j:
                    continue
                route[i], route[j] = route[j], route[i]
                new_sol = canonical((tuple(route),))
                if new_sol != original:
                    return new_sol
                route[i], route[j] = route[j], route[i]

        # Fallback determinista para garantizar cambio cuando exista al menos un movimiento posible.
        if len(routes) >= 2:
            for r1 in range(len(routes)):
                if not routes[r1]:
                    continue
                for r2 in range(r1 + 1, len(routes)):
                    if not routes[r2]:
                        continue
                    for i1, c1 in enumerate(routes[r1]):
                        for i2, c2 in enumerate(routes[r2]):
                            if c1 != c2:
                                routes[r1][i1], routes[r2][i2] = c2, c1
                                new_sol = canonical(tuple(tuple(r) for r in routes))
                                if new_sol != original:
                                    return new_sol
                                routes[r1][i1], routes[r2][i2] = c1, c2
            return sol

        route = routes[0]
        if len(route) >= 2:
            i, j = 0, 1
            route[i], route[j] = route[j], route[i]
            new_sol = canonical((tuple(route),))
            if new_sol != original:
                return new_sol
            route[i], route[j] = route[j], route[i]

        return sol


def build_component(problem, **params):
    _strength = params.get("strength", 3.0)
    return CrossRouteSwapPerturbation(problem)
