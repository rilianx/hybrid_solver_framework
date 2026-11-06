"""El modelo de referencia del flow shop de permutación con makespan, como piezas (`core.model_parts`): genera los casos
de prueba (`cases.py`) y es el oráculo de los casos ocultos al validar el modelo C++ que escribe el LLM. No lo ve el LLM.

Solución: `((j0, j1, ..., j_{n-1}),)`, una sola fila con el orden de los trabajos. Familias: `permutacion` (trabajos que
faltan, sobran o no existen). Término: `makespan` (instante en que el último trabajo de la secuencia termina en la
última máquina), calculado sobre la secuencia tal como viene, saltando los índices que no existen.
"""

from __future__ import annotations

from examples.flowshop.model_parts import (  # noqa: F401
    canonical, from_answer, random_solution, trivial_solution, violations, well_formed)

from examples.flowshop.instance import PFSPInstance


def cost_terms(inst: PFSPInstance, sol) -> dict[str, float]:
    m, n = inst.n_machines, inst.n_jobs
    c = [0] * m
    for j in (j for row in sol for j in row):
        if not 0 <= j < n:
            continue
        c[0] += inst.p[0][j]
        for i in range(1, m):
            c[i] = max(c[i], c[i - 1]) + inst.p[i][j]
    return {"makespan": float(c[m - 1])}
