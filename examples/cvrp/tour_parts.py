"""El CVRP con otra representación: GRAN TOUR + Split (Prins, 2004). Referencia de la variante
`cvrp_tour` (ver `tour_pack.py`).

La solución es una permutación de los clientes; `split` la corta de forma óptima en rutas que
respetan la capacidad (camino mínimo en un grafo acíclico). Toda permutación se decodifica a una
solución factible en capacidad, los vecindarios son los de permutaciones (intercambio, inserción,
2-opt sobre el tour) y el costo de una permutación es el de su mejor corte.

Para el framework es un problema distinto de `cvrp` (otro pack, otros componentes), con la misma
instancia, los mismos casos de prueba y la misma vista MIP: por eso sus resultados se comparan
directamente con los de `cvrp`. Es una representación con decodificador (`ModelSpec.decoder`):
from_answer concatena las rutas de la respuesta y Split puede cortarlas mejor.
"""

from __future__ import annotations

from functools import lru_cache
from random import Random

from . import model_parts as routes
from .instance import CVRPInstance


def canonical(sol):
    return tuple(int(c) for c in sol)


def trivial_solution(inst: CVRPInstance):
    return tuple(inst.customers)


def random_solution(inst: CVRPInstance, rng: Random):
    tour = list(inst.customers)
    rng.shuffle(tour)
    return tuple(tour)


def from_answer(inst: CVRPInstance, answer):
    return tuple(int(c) for r in answer for c in r)


@lru_cache(maxsize=8192)
def split(inst: CVRPInstance, tour: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Corte óptimo del tour en rutas de carga <= capacidad (O(n²) en el peor caso)."""
    n = len(tour)
    best = [0.0] + [float("inf")] * n
    pred = [0] * (n + 1)
    for i in range(n):
        if best[i] == float("inf"):
            continue
        load, path = 0.0, 0.0
        for j in range(i, n):
            c = tour[j]
            load += inst.demand[c]
            if j > i and load > inst.capacity:
                break
            path = inst.dist(0, c) if j == i else path + inst.dist(tour[j - 1], c)
            total = best[i] + path + inst.dist(c, 0)
            if total < best[j + 1] - 1e-12:
                best[j + 1], pred[j + 1] = total, i
    out, j = [], n
    while j > 0:
        i = pred[j]
        out.append(tuple(tour[i:j]))
        j = i
    return routes.canonical(out)


def decode(inst: CVRPInstance, tour):
    return split(inst, canonical(tour))


def violations(inst: CVRPInstance, sol) -> dict[str, float]:
    return routes.violations(inst, decode(inst, sol))


def cost_terms(inst: CVRPInstance, sol) -> dict[str, float]:
    return routes.cost_terms(inst, decode(inst, sol))


# ---------------------------------------------------------------- vista MIP (la de rutas)
variables = routes.variables
structural_variables = routes.structural_variables
constraint_families = routes.constraint_families
objective_terms = routes.objective_terms
variable_groups = routes.variable_groups


def to_assignment(inst: CVRPInstance, sol):
    return routes.to_assignment(inst, decode(inst, sol))


def aux_values(inst: CVRPInstance, sol):
    return routes.aux_values(inst, decode(inst, sol))


def from_assignment(inst: CVRPInstance, x):
    return tuple(c for r in routes.from_assignment(inst, x) for c in r)


# ---------------------------------------------------------------- vista constructiva
# Parcial: el prefijo del tour. Acción: el cliente que se agrega al final. Toda permutación se
# decodifica a una solución factible, así que nunca hay callejón sin salida.
def empty_partial(inst: CVRPInstance):
    return ()


def candidates(inst: CVRPInstance, partial):
    used = set(partial)
    return [c for c in inst.customers if c not in used]


def apply_action(inst: CVRPInstance, partial, action):
    return (*partial, action)


def is_complete(inst: CVRPInstance, partial) -> bool:
    return len(partial) == inst.n_customers


def to_solution(inst: CVRPInstance, partial):
    return canonical(partial)


def complete_partial(inst: CVRPInstance, partial, rng):
    return canonical((*partial, *candidates(inst, partial)))
