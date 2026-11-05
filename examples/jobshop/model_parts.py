"""El oráculo del job shop (makespan) (`core.model_parts`, vista heurística): la referencia contra la que se valida lo
que escribe el LLM y con la que se generan los casos de prueba (`cases.py`).

Representación y formato neutral de respuesta (el de los casos): una secuencia por máquina, la
lista de trabajos en el orden en que esa máquina los procesa. El plan es el semiactivo: cada
operación empieza apenas terminan la anterior de su trabajo y la anterior de su máquina. Familias:
`secuencia` (cada máquina procesa exactamente una vez a cada trabajo que pasa por ella) y `orden`
(las secuencias no forman un ciclo con las rutas de los trabajos; si lo forman no hay plan). Término
del objetivo: `makespan`.

La vista MIP la escribe el LLM (`llm.native_mip_generator`, `generated/jobshop_native/mip/mip.py`).
"""

from __future__ import annotations

from random import Random

from .instance import JSSPInstance


def canonical(sol):
    return tuple(tuple(int(j) for j in seq) for seq in sol)


def jobs_on(inst: JSSPInstance, m: int) -> list[int]:
    return [j for j in inst.jobs if inst.op_index(j, m) is not None]


def trivial_solution(inst: JSSPInstance):
    """Todas las máquinas en el orden de los trabajos: nunca forma un ciclo."""
    return canonical(jobs_on(inst, m) for m in inst.machines)


def from_answer(inst: JSSPInstance, answer):
    return canonical(answer)


def schedule(inst: JSSPInstance, sol):
    """Plan semiactivo de las secuencias: (inicios[j][k], makespan, operaciones liberadas).

    Recorre las operaciones en orden topológico. Si las secuencias forman un ciclo, se traba:
    entonces libera la operación pendiente de menor trabajo entre las que ya tienen hecha la anterior
    de su trabajo (ignora su predecesora en la máquina) y la cuenta. `liberadas > 0` si y solo si hay
    ciclo. En una secuencia, los trabajos repetidos o ajenos se ignoran (cuenta la primera aparición).
    """
    mpred: dict[tuple[int, int], tuple[int, int]] = {}
    msucc: dict[tuple[int, int], tuple[int, int]] = {}
    for m, seq in enumerate(sol[:inst.n_machines]):
        prev, seen = None, set()
        for j in seq:
            if j in seen or not 0 <= j < inst.n_jobs:
                continue
            k = inst.op_index(j, m)
            if k is None:
                continue
            seen.add(j)
            if prev is not None:
                mpred[(j, k)], msucc[prev] = prev, (j, k)
            prev = (j, k)
    start = [[0] * len(r) for r in inst.routes]
    end = [[0] * len(r) for r in inst.routes]
    done = [0] * inst.n_jobs  # operaciones hechas de cada trabajo
    indeg = {(j, k): (k > 0) + ((j, k) in mpred) for j in inst.jobs for k in range(len(inst.routes[j]))}
    ready = sorted(op for op, d in indeg.items() if d == 0)
    total, n_done, released = len(indeg), 0, 0
    finished: set[tuple[int, int]] = set()
    while n_done < total:
        if not ready:  # ciclo: liberar una operación
            j = min(j for j in inst.jobs if done[j] < len(inst.routes[j]))
            ready = [(j, done[j])]
            released += 1
        op = ready.pop()
        if op in finished:
            continue
        j, k = op
        s = end[j][k - 1] if k > 0 else 0
        if op in mpred and mpred[op] in finished:
            s = max(s, end[mpred[op][0]][mpred[op][1]])
        start[j][k], end[j][k] = s, s + inst.proc(j, k)
        finished.add(op)
        done[j] += 1
        n_done += 1
        for nxt in ((j, k + 1) if k + 1 < len(inst.routes[j]) else None, msucc.get(op)):
            if nxt is not None and nxt not in finished:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)
    makespan = max((end[j][-1] for j in inst.jobs if inst.routes[j]), default=0)
    return start, makespan, released


def random_solution(inst: JSSPInstance, rng: Random):
    """Despacho al azar: en cada paso, la próxima operación de un trabajo al azar va al final de su
    máquina. Nunca forma un ciclo."""
    seqs = [[] for _ in inst.machines]
    nxt = [0] * inst.n_jobs
    pending = [j for j in inst.jobs for _ in inst.routes[j]]
    rng.shuffle(pending)
    for j in pending:
        seqs[inst.machine(j, nxt[j])].append(j)
        nxt[j] += 1
    return canonical(seqs)


def _sequence_errors(inst: JSSPInstance, sol) -> int:
    bad = 0
    for m in inst.machines:
        seq = sol[m] if m < len(sol) else ()
        want = set(jobs_on(inst, m))
        seen: dict[int, int] = {}
        for j in seq:
            seen[j] = seen.get(j, 0) + 1
        bad += sum(abs(seen.get(j, 0) - 1) for j in want) + sum(c for j, c in seen.items() if j not in want)
    return bad + sum(len(seq) for seq in sol[inst.n_machines:])


def violations(inst: JSSPInstance, sol) -> dict[str, float]:
    return {"secuencia": float(_sequence_errors(inst, sol)), "orden": float(schedule(inst, sol)[2])}


def cost_terms(inst: JSSPInstance, sol) -> dict[str, float]:
    return {"makespan": float(schedule(inst, sol)[1])}


def critical_path(inst: JSSPInstance, sol, start=None) -> list[tuple[int, int]]:
    """Un camino crítico del plan semiactivo (operaciones (j, k) en orden), hacia atrás desde la que
    termina última: cada operación empieza cuando termina la anterior de su trabajo o de su máquina."""
    if start is None:
        start = schedule(inst, sol)[0]
    pos = {}
    for m, seq in enumerate(sol):
        for i, j in enumerate(seq):
            pos.setdefault((m, j), i)
    j = max(inst.jobs, key=lambda j: start[j][-1] + inst.proc(j, len(inst.routes[j]) - 1))
    op = (j, len(inst.routes[j]) - 1)
    path = [op]
    while start[op[0]][op[1]] > 0:
        j, k = op
        m, s = inst.machine(j, k), start[j][k]
        i = pos.get((m, j))
        if i is not None and i > 0:
            pj = sol[m][i - 1]
            pk = inst.op_index(pj, m) if 0 <= pj < inst.n_jobs else None
            if pk is not None and start[pj][pk] + inst.proc(pj, pk) == s:
                op = (pj, pk)
                path.append(op)
                continue
        if k > 0 and start[j][k - 1] + inst.proc(j, k - 1) == s:
            op = (j, k - 1)
            path.append(op)
            continue
        break
    return path[::-1]


def critical_blocks(inst: JSSPInstance, sol, start=None) -> list[tuple[int, list[int]]]:
    """Los bloques del camino crítico: (máquina, trabajos consecutivos en esa máquina), de 2 o más."""
    blocks: list[tuple[int, list[int]]] = []
    for j, k in critical_path(inst, sol, start):
        m = inst.machine(j, k)
        if blocks and blocks[-1][0] == m:
            blocks[-1][1].append(j)
        else:
            blocks.append((m, [j]))
    return [b for b in blocks if len(b[1]) > 1]
