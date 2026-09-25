from __future__ import annotations

from random import Random
from typing import Any

from examples.cvrp.problem_model import canonical


COMPONENT = {
    "name": "radial_sector_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment", "ProblemModel.inst", "ProblemModel.variable_groups"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RadialSectorDestruction:
    """Libera una ruta completa o un tramo dominante de una ruta, priorizando estructura de carga/recorrido."""

    def __init__(self, problem, inst):
        self.problem = problem
        self.inst = inst

    def destroy(self, sol, ratio: float, rng: Random) -> tuple[Any, set[str]]:
        assignment = self.problem.to_assignment(sol)
        routes = list(sol)
        if not routes:
            return assignment, set()

        # Selecciona una ruta larga con sesgo aleatorio: destruye estructura de una ruta completa.
        route_sizes = [len(r) for r in routes]
        max_size = max(route_sizes)
        candidates = [r for r in routes if len(r) >= max(1, int(round((1.0 - ratio) * max_size)))]
        route = candidates[rng.randrange(len(candidates))] if candidates else routes[rng.randrange(len(routes))]

        # Tamaño objetivo de destrucción: fracción de clientes de la ruta seleccionada.
        k = max(1, min(len(route), int(round(ratio * len(route)))))

        # Si la ruta es corta, liberar toda la ruta; si es larga, liberar un bloque contiguo de clientes.
        if k >= len(route):
            removed = set(route)
        else:
            start = rng.randrange(len(route))
            removed = {route[(start + t) % len(route)] for t in range(k)}

        free_vars: set[str] = set()
        for name in assignment:
            _, a, b = name.split("_")
            i, j = int(a), int(b)
            if (i in removed) or (j in removed):
                free_vars.add(name)

        # Garantía de no quedarse sin variables libres.
        if not free_vars:
            c = route[0]
            for j in range(self.inst.n_customers + 1):
                if j != c:
                    free_vars.add(f"x_{c}_{j}")
                    free_vars.add(f"x_{j}_{c}")

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, **params):
    return RadialSectorDestruction(problem, problem.inst)
