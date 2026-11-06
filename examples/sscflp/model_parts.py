"""El oráculo del SSCFLP (`core.model_parts`, vista heurística): la referencia contra la que se valida lo que escribe el
LLM y con la que se generan los casos de prueba (`cases.py`).

Formato neutral de respuesta (el de los casos): una lista de m enteros, el centro (0..n-1) que atiende a cada cliente
(-1: sin atender). Un centro está abierto si y solo si atiende a algún cliente. Familias: `asignacion` (cada cliente atendido por
exactamente un centro) y `capacidad` (demanda asignada a cada centro <= su capacidad). Términos del objetivo:
`apertura` (costos fijos de los centros abiertos) y `transporte` (costos de asignación).

La vista MIP la escribe el LLM (`llm.native_mip_generator`).
"""

from __future__ import annotations

from random import Random

from .instance import SSCFLPInstance


def canonical(sol):
    return tuple(int(i) for i in sol)


def trivial_solution(inst: SSCFLPInstance):
    """Clientes de mayor a menor demanda, cada uno al centro más barato con capacidad libre; si alguno no cabe, first
    fit decreasing en los centros de mayor capacidad (bin packing). Factible en todas las instancias del benchmark y
    en las generadas (`pack.make_instances` descarta las que no)."""
    for sol in (_greedy_by_cost(inst), _first_fit_decreasing(inst)):
        if sol is not None:
            return canonical(sol)
    raise ValueError("no se encontró una asignación factible con las heurísticas triviales")


def _greedy_by_cost(inst: SSCFLPInstance):
    left = list(inst.capacity)
    sol = [-1] * inst.n_customers
    for j in sorted(inst.customers, key=lambda j: (-inst.demand[j], j)):
        fits = [i for i in inst.facilities if left[i] >= inst.demand[j]]
        if not fits:
            return None
        i = min(fits, key=lambda i: (inst.cost[i][j], i))
        sol[j], left[i] = i, left[i] - inst.demand[j]
    return sol


def _first_fit_decreasing(inst: SSCFLPInstance):
    left = list(inst.capacity)
    order = sorted(inst.facilities, key=lambda i: (-inst.capacity[i], i))
    sol = [-1] * inst.n_customers
    for j in sorted(inst.customers, key=lambda j: (-inst.demand[j], j)):
        i = next((i for i in order if left[i] >= inst.demand[j]), None)
        if i is None:
            return None
        sol[j], left[i] = i, left[i] - inst.demand[j]
    return sol


def random_solution(inst: SSCFLPInstance, rng: Random):
    """Se abre un subconjunto al azar de centros y cada cliente va a uno de ellos al azar (puede violar capacidad)."""
    k = rng.randint(1, inst.n_facilities)
    open_ = rng.sample(list(inst.facilities), k)
    return canonical(rng.choice(open_) for _ in inst.customers)


def from_answer(inst: SSCFLPInstance, answer):
    return canonical(answer)


def violations(inst: SSCFLPInstance, sol) -> dict[str, float]:
    n, m = inst.n_facilities, inst.n_customers
    bad = abs(len(sol) - m) + sum(1 for i in sol[:m] if not 0 <= i < n)
    load = [0.0] * n
    for j, i in enumerate(sol[:m]):
        if 0 <= i < n:
            load[i] += inst.demand[j]
    cap = sum(max(0.0, load[i] - inst.capacity[i]) for i in inst.facilities)
    return {"asignacion": float(bad), "capacidad": float(cap)}


def cost_terms(inst: SSCFLPInstance, sol) -> dict[str, float]:
    n, m = inst.n_facilities, inst.n_customers
    used = {i for i in sol[:m] if 0 <= i < n}
    return {"apertura": float(sum(inst.fixed[i] for i in used)),
            "transporte": float(sum(inst.cost[i][j] for j, i in enumerate(sol[:m]) if 0 <= i < n))}
