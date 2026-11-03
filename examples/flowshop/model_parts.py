"""El modelo de referencia del flow shop de permutación con flowtime total, como piezas (`core.model_parts`): genera
los casos de prueba (`cases.py`) y es el oráculo de los casos ocultos al validar el modelo C++ que escribe el LLM. No lo
ve el LLM.

Solución: `((j0, j1, ..., j_{n-1}),)`, una sola fila con el orden de los trabajos (la forma de la respuesta). Familias:
`permutacion` (trabajos que faltan, sobran o no existen). Término: `flowtime` (suma de los instantes de término de los
trabajos en la última máquina), calculado sobre la secuencia tal como viene, saltando los índices que no existen.
"""

from __future__ import annotations

from random import Random

from .instance import PFSPInstance


def canonical(sol):
    return tuple(tuple(int(j) for j in row) for row in sol)


def trivial_solution(inst: PFSPInstance):
    return ((*range(inst.n_jobs),),)


def random_solution(inst: PFSPInstance, rng: Random):
    perm = list(range(inst.n_jobs))
    rng.shuffle(perm)
    return (tuple(perm),)


def from_answer(inst: PFSPInstance, answer):
    return canonical(answer)


def violations(inst: PFSPInstance, sol) -> dict[str, float]:
    n = inst.n_jobs
    seq = [j for row in sol for j in row]
    count = [0] * n
    bad = 0
    for j in seq:
        if 0 <= j < n:
            count[j] += 1
        else:
            bad += 1
    return {"permutacion": float(sum(abs(c - 1) for c in count) + bad)}


def cost_terms(inst: PFSPInstance, sol) -> dict[str, float]:
    m, n = inst.n_machines, inst.n_jobs
    c = [0] * m
    total = 0
    for j in (j for row in sol for j in row):
        if not 0 <= j < n:
            continue
        c[0] += inst.p[0][j]
        for i in range(1, m):
            c[i] = max(c[i], c[i - 1]) + inst.p[i][j]
        total += c[m - 1]
    return {"flowtime": float(total)}
