"""El oráculo de la mochila multidimensional (`core.model_parts`, vista heurística): la referencia contra la que se valida lo
que escribe el LLM y con la que se generan los casos de prueba (`cases.py`).

Formato neutral de respuesta (el de los casos): una lista con UNA sola lista de n ceros y unos, 1 si el ítem j va en la
mochila; el contrato del modelo C++ es una lista de listas (como el flow shop). Familia:
`capacidad` (consumo de cada recurso <= su capacidad; magnitud = recursos excedidos más el exceso relativo, así toda
violación es al menos 1). Término del objetivo: `beneficio`, el beneficio total con signo menos (el framework minimiza).

La vista MIP la escribe el LLM (`llm.native_mip_generator`).
"""

from __future__ import annotations

from random import Random

from .instance import MKPInstance


def canonical(sol):
    return (tuple(1 if int(x) else 0 for x in sol[0]),)


def wrap(selection) -> tuple:
    """Una selección plana (0/1 por ítem) en la forma de la solución."""
    return canonical([selection])


def trivial_solution(inst: MKPInstance):
    """Greedy: ítems por beneficio / consumo relativo (Σ_i consumo / capacidad), cada uno si cabe. La mochila vacía
    también es factible, pero la greedy hace que la penalización (10 · (|costo de la trivial| + 1)) escale con los
    beneficios."""
    def ratio(j):
        use = sum(inst.weight[i][j] / inst.capacity[i] for i in inst.resources if inst.capacity[i] > 0)
        return inst.profit[j] / use if use > 0 else float("inf")

    left = list(inst.capacity)
    sol = [0] * inst.n_items
    for j in sorted(inst.items, key=lambda j: (-ratio(j), j)):
        if all(inst.weight[i][j] <= left[i] for i in inst.resources):
            sol[j] = 1
            for i in inst.resources:
                left[i] -= inst.weight[i][j]
    return wrap(sol)


def random_solution(inst: MKPInstance, rng: Random):
    """Cada ítem con una probabilidad al azar (puede violar capacidad)."""
    p = rng.random()
    return wrap([rng.random() < p for _ in inst.items])


def from_answer(inst: MKPInstance, answer):
    return canonical(answer)


def violations(inst: MKPInstance, sol) -> dict[str, float]:
    sol = sol[0]
    exc = 0.0
    for i in inst.resources:
        use = sum(inst.weight[i][j] for j in inst.items if sol[j])
        if use > inst.capacity[i] + 1e-9:
            exc += 1.0 + (use - inst.capacity[i]) / max(inst.capacity[i], 1.0)
    return {"capacidad": exc}


def cost_terms(inst: MKPInstance, sol) -> dict[str, float]:
    sol = sol[0]
    return {"beneficio": -float(sum(inst.profit[j] for j in inst.items if sol[j]))}
