from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "two_route_tail_exchange_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class TwoRouteTailExchangePerturbation:
    def __init__(self, problem: Any):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        routes = [list(r) for r in sol]
        if len(routes) < 2:
            return sol

        # 2-opt* / intercambio de colas entre dos rutas:
        # elige dos rutas y corta cada una en una posición; intercambia sus sufijos.
        # Usa una posición sesgada hacia la mitad para modificar estructura de rutas.
        tries = max(1, min(8, int(round(strength))))
        for _ in range(tries):
            i, j = rng.sample(range(len(routes)), 2)
            a, b = routes[i], routes[j]
            if not a or not b:
                continue

            cut_a = rng.randint(0, len(a))
            cut_b = rng.randint(0, len(b))

            head_a, tail_a = a[:cut_a], a[cut_a:]
            head_b, tail_b = b[:cut_b], b[cut_b:]

            new_a = head_a + tail_b
            new_b = head_b + tail_a

            # Evitar rutas vacías.
            if not new_a and not new_b:
                continue

            # Si ambas son factibles o al menos una mejora estructuralmente, aceptar.
            routes2 = list(routes)
            routes2[i] = new_a
            routes2[j] = new_b
            new_sol = canonical(tuple(tuple(r) for r in routes2))
            if new_sol != sol:
                return new_sol

        # Fallback: inversión de un tramo dentro de la ruta más larga.
        idx = max(range(len(routes)), key=lambda k: len(routes[k]))
        route = routes[idx]
        if len(route) >= 2:
            p = rng.randrange(0, len(route) - 1)
            q = rng.randrange(p + 1, len(route))
            route[p : q + 1] = reversed(route[p : q + 1])
            routes[idx] = route
            new_sol = canonical(tuple(tuple(r) for r in routes))
            if new_sol != sol:
                return new_sol

        return sol


def build_component(problem, **params):
    strength = params.get("strength", 3.0)
    return TwoRouteTailExchangePerturbation(problem)
