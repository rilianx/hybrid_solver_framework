from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "radial_reinsert_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "strength": {"type": "float", "range": [1.0, 10.0]},
    },
}


class RadialReinsertPerturbation:
    def __init__(self, problem: Any):
        self.problem = problem

    def perturb(self, sol, strength: float, rng: Random):
        inst = self.problem.inst
        customers = [c for route in sol for c in route]
        n = len(customers)
        if n <= 1:
            return sol

        k = max(1, min(n, int(round(strength))))
        seed = rng.choice(customers)

        # Selecciona k clientes más cercanos al seed, con algo de aleatoriedad.
        scored = []
        sx, sy = inst.coords[seed]
        for c in customers:
            x, y = inst.coords[c]
            d = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
            scored.append((d + 0.15 * rng.random(), c))
        scored.sort()
        removed = set(c for _, c in scored[:k])

        if len(removed) == n:
            # Deja al menos uno para reconstruir desde la solución original.
            removed.pop()

        remaining_routes = []
        removed_list = []
        for route in sol:
            kept = []
            for c in route:
                if c in removed:
                    removed_list.append(c)
                else:
                    kept.append(c)
            if kept:
                remaining_routes.append(tuple(kept))

        # Reinsertar clientes en el mejor lugar local según desvío incremental.
        routes = [list(r) for r in remaining_routes]
        for c in removed_list:
            best = None
            best_pos = None
            for ridx, route in enumerate(routes):
                # probar inserciones en todas las posiciones, incluyendo extremos
                for pos in range(len(route) + 1):
                    prev = 0 if pos == 0 else route[pos - 1]
                    nxt = 0 if pos == len(route) else route[pos]
                    delta = (
                        inst.dist(prev, c)
                        + inst.dist(c, nxt)
                        - inst.dist(prev, nxt)
                    )
                    # pequeña preferencia por rutas con carga holgada
                    load = sum(inst.demand[x] for x in route)
                    slack = max(0.0, inst.capacity - load)
                    score = delta - 1e-6 * slack
                    if best is None or score < best:
                        best = score
                        best_pos = (ridx, pos)
            # si ninguna ruta existente conviene, abre una nueva
            if best_pos is None or (best is not None and len(routes) > 0 and best > 0 and rng.random() < 0.2):
                routes.append([c])
            else:
                ridx, pos = best_pos
                routes[ridx].insert(pos, c)

        new_sol = canonical(tuple(tuple(r) for r in routes))
        if new_sol == sol:
            # Forzar cambio mínimo: mover un cliente entre rutas si es posible.
            if len(sol) >= 2:
                r1 = rng.randrange(len(sol))
                r2 = (r1 + 1) % len(sol)
                if sol[r1]:
                    c = sol[r1][0]
                    routes = [list(r) for r in sol]
                    routes[r1].pop(0)
                    routes[r2].append(c)
                    new_sol = canonical(tuple(tuple(r) for r in routes))
        return new_sol


def build_component(problem, **params):
    strength = params.get("strength", 3.0)
    return RadialReinsertPerturbation(problem)
