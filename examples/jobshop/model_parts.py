"""El job shop (makespan) escrito como piezas (`core.model_parts`): la referencia de la variante
`sequences` y con la que se generan los casos de prueba (`cases.py`).

Representación y formato neutral de respuesta (el de los casos): una secuencia por máquina, la
lista de trabajos en el orden en que esa máquina los procesa. El plan es el semiactivo: cada
operación empieza apenas terminan la anterior de su trabajo y la anterior de su máquina. Familias:
`secuencia` (cada máquina procesa exactamente una vez a cada trabajo que pasa por ella) y `orden`
(las secuencias no forman un ciclo con las rutas de los trabajos; si lo forman no hay plan). Término
del objetivo: `makespan`.

MIP disyuntivo: binarias `y_m_i_j` (estructurales; i antes que j en la máquina m), inicios `s_j_k` y
makespan `C` continuos. Familias `secuencia.par` (y_mij + y_mji = 1), `orden.ruta` (precedencias de
cada trabajo), `orden.maquina` (big-M con M = suma de tiempos) y `orden.fin` (C >= fin de cada trabajo).
"""

from __future__ import annotations

from random import Random
from typing import NamedTuple

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


# ---------------------------------------------------------------- vista MIP
def _y(m, i, j):
    return f"y_{m}_{i}_{j}"


def _s(j, k):
    return f"s_{j}_{k}"


def structural_variables(inst: JSSPInstance):
    out = []
    for m in inst.machines:
        js = jobs_on(inst, m)
        out += [_y(m, i, j) for i in js for j in js if i != j]
    return out


def variables(inst: JSSPInstance):
    H = float(inst.horizon())
    out = {v: (0.0, 1.0, "binary") for v in structural_variables(inst)}
    out.update({_s(j, k): (0.0, H, "continuous") for j in inst.jobs for k in range(len(inst.routes[j]))})
    out["C"] = (0.0, H, "continuous")
    return out


def to_assignment(inst: JSSPInstance, sol):
    x = {v: 0.0 for v in structural_variables(inst)}
    for m, seq in enumerate(sol[:inst.n_machines]):
        first: list[int] = []
        for j in seq:
            if j not in first and inst.op_index(j, m) is not None:
                first.append(j)
        for a, i in enumerate(first):
            for j in first[a + 1:]:
                x[_y(m, i, j)] = 1.0
    return x


def aux_values(inst: JSSPInstance, sol):
    start, makespan, _ = schedule(inst, sol)
    out = {_s(j, k): float(start[j][k]) for j in inst.jobs for k in range(len(inst.routes[j]))}
    out["C"] = float(makespan)
    return out


def from_assignment(inst: JSSPInstance, x):
    seqs = []
    for m in inst.machines:
        js = jobs_on(inst, m)
        before = {j: sum(1 for i in js if i != j and round(x.get(_y(m, i, j)) or 0.0) >= 1) for j in js}
        seqs.append(sorted(js, key=lambda j: (before[j], j)))
    return canonical(seqs)


def constraint_families(inst: JSSPInstance):
    H = float(inst.horizon())
    par, ruta, maq, fin = [], [], [], []
    for m in inst.machines:
        js = jobs_on(inst, m)
        for a, i in enumerate(js):
            for j in js[a + 1:]:
                par.append(({_y(m, i, j): 1.0, _y(m, j, i): 1.0}, "==", 1.0))
        for i in js:
            for j in js:
                if i != j:  # i antes que j en m: s_j >= s_i + p_i
                    ki, kj = inst.op_index(i, m), inst.op_index(j, m)
                    maq.append(({_s(j, kj): 1.0, _s(i, ki): -1.0, _y(m, i, j): -H}, ">=", inst.proc(i, ki) - H))
    for j in inst.jobs:
        for k in range(len(inst.routes[j]) - 1):
            ruta.append(({_s(j, k + 1): 1.0, _s(j, k): -1.0}, ">=", float(inst.proc(j, k))))
        last = len(inst.routes[j]) - 1
        fin.append(({"C": 1.0, _s(j, last): -1.0}, ">=", float(inst.proc(j, last))))
    return {"secuencia.par": par, "orden.ruta": ruta, "orden.maquina": maq, "orden.fin": fin}


def objective_terms(inst: JSSPInstance):
    return {"makespan": ({"C": 1.0}, 0.0)}


def variable_groups(inst: JSSPInstance):
    """Una por máquina: Fix-and-Optimize reordena unas máquinas con las demás fijas."""
    return {f"m{m}": [_y(m, i, j) for i in jobs_on(inst, m) for j in jobs_on(inst, m) if i != j] for m in inst.machines}


# ---------------------------------------------------------------- vista constructiva
# Despacho: en cada paso se agenda la próxima operación de un trabajo al final de su máquina (el plan
# semiactivo se arma en orden). Cualquier orden de despacho da secuencias sin ciclos.
class JSSPPartial(NamedTuple):
    """Estado parcial (inmutable). Atributos que puede leer un puntaje:
      seqs[m]          trabajos ya secuenciados en la máquina m, en orden
      nxt[j]           índice de la próxima operación del trabajo j (== len(routes[j]) si terminó)
      job_ready[j]     cuándo termina la última operación agendada del trabajo j
      mach_ready[m]    cuándo queda libre la máquina m
      order            trabajos en el orden en que se despacharon sus operaciones
    """

    seqs: tuple[tuple[int, ...], ...]
    nxt: tuple[int, ...]
    job_ready: tuple[int, ...]
    mach_ready: tuple[int, ...]
    order: tuple[int, ...]


class Dispatch(NamedTuple):
    """Agendar la operación `op` del trabajo `job` en la máquina `machine`, de `start` a `end`."""

    job: int
    op: int
    machine: int
    start: int
    end: int


def empty_partial(inst: JSSPInstance):
    return JSSPPartial(tuple(() for _ in inst.machines), (0,) * inst.n_jobs, (0,) * inst.n_jobs,
                       (0,) * inst.n_machines, ())


def candidates(inst: JSSPInstance, partial):
    out = []
    for j in inst.jobs:
        k = partial.nxt[j]
        if k < len(inst.routes[j]):
            m, p = inst.routes[j][k]
            s = max(partial.job_ready[j], partial.mach_ready[m])
            out.append(Dispatch(j, k, m, s, s + p))
    return out


def apply_action(inst: JSSPInstance, partial, action):
    j, k, m, _, e = action
    seqs = list(partial.seqs)
    seqs[m] = (*seqs[m], j)
    nxt, jr, mr = list(partial.nxt), list(partial.job_ready), list(partial.mach_ready)
    nxt[j], jr[j], mr[m] = k + 1, e, e
    return JSSPPartial(tuple(seqs), tuple(nxt), tuple(jr), tuple(mr), (*partial.order, j))


def is_complete(inst: JSSPInstance, partial) -> bool:
    return all(partial.nxt[j] >= len(inst.routes[j]) for j in inst.jobs)


def to_solution(inst: JSSPInstance, partial):
    return canonical(partial.seqs)


def complete_partial(inst: JSSPInstance, partial, rng):
    while not is_complete(inst, partial):
        partial = apply_action(inst, partial, candidates(inst, partial)[0])
    return to_solution(inst, partial)
