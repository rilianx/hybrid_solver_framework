"""El job shop con otra representación: PERMUTACIÓN CON REPETICIÓN (Bierwirth, 1995). Referencia de
la variante `operations`.

La solución es una tupla de trabajos donde cada trabajo aparece tantas veces como operaciones tiene;
la k-ésima aparición del trabajo j es su operación k. Se decodifica agregando cada operación, en ese
orden, al final de su máquina: toda permutación da secuencias sin ciclos, así que toda solución es
factible y los vecindarios son los de permutaciones. Varias permutaciones dan las mismas secuencias.

Misma instancia, mismos casos y misma vista MIP que la variante `sequences` (`model_parts`), así que
sus resultados se comparan directamente. Es una representación con decodificador (`ModelSpec.decoder`):
from_answer devuelve un orden topológico de las secuencias de la respuesta (si tienen un ciclo no
son representables y la decodificación es otra, factible).
"""

from __future__ import annotations

from random import Random

from . import model_parts as seq
from .instance import JSSPInstance


def canonical(sol):
    return tuple(int(j) for j in sol)


def trivial_solution(inst: JSSPInstance):
    """Ronda por los trabajos: la operación 0 de todos, después la 1, etc."""
    depth = max(len(r) for r in inst.routes)
    return tuple(j for k in range(depth) for j in inst.jobs if k < len(inst.routes[j]))


def random_solution(inst: JSSPInstance, rng: Random):
    out = [j for j in inst.jobs for _ in inst.routes[j]]
    rng.shuffle(out)
    return tuple(out)


def decode(inst: JSSPInstance, sol):
    """Las secuencias por máquina; las apariciones de más de un trabajo se ignoran."""
    seqs = [[] for _ in inst.machines]
    nxt = [0] * inst.n_jobs
    for j in sol:
        if 0 <= j < inst.n_jobs and nxt[j] < len(inst.routes[j]):
            seqs[inst.machine(j, nxt[j])].append(j)
            nxt[j] += 1
    return seq.canonical(seqs)


def _topological(inst: JSSPInstance, seqs):
    """Un orden de despacho de las secuencias (el de su plan semiactivo, por inicio y trabajo)."""
    start, _, _ = seq.schedule(inst, seqs)
    ops = sorted(((start[j][k], j, k) for j in inst.jobs for k in range(len(inst.routes[j]))))
    return tuple(j for _, j, _ in ops)


def from_answer(inst: JSSPInstance, answer):
    return _topological(inst, seq.canonical(answer))


def _extra(inst: JSSPInstance, sol) -> int:
    count = [0] * inst.n_jobs
    foreign = 0
    for j in sol:
        if 0 <= j < inst.n_jobs:
            count[j] += 1
        else:
            foreign += 1
    return foreign + sum(abs(count[j] - len(inst.routes[j])) for j in inst.jobs)


def violations(inst: JSSPInstance, sol) -> dict[str, float]:
    v = seq.violations(inst, decode(inst, sol))
    v["secuencia"] = float(_extra(inst, sol))
    return v


def cost_terms(inst: JSSPInstance, sol) -> dict[str, float]:
    return seq.cost_terms(inst, decode(inst, sol))


# ---------------------------------------------------------------- vista MIP (la de secuencias)
variables = seq.variables
structural_variables = seq.structural_variables
constraint_families = seq.constraint_families
objective_terms = seq.objective_terms
variable_groups = seq.variable_groups


def to_assignment(inst: JSSPInstance, sol):
    return seq.to_assignment(inst, decode(inst, sol))


def aux_values(inst: JSSPInstance, sol):
    return seq.aux_values(inst, decode(inst, sol))


def from_assignment(inst: JSSPInstance, x):
    return _topological(inst, seq.from_assignment(inst, x))


# ---------------------------------------------------------------- vista constructiva (la de secuencias)
JSSPPartial, Dispatch = seq.JSSPPartial, seq.Dispatch
empty_partial = seq.empty_partial
candidates = seq.candidates
apply_action = seq.apply_action
is_complete = seq.is_complete


def to_solution(inst: JSSPInstance, partial):
    return canonical(partial.order)


def complete_partial(inst: JSSPInstance, partial, rng):
    while not is_complete(inst, partial):
        partial = apply_action(inst, partial, candidates(inst, partial)[0])
    return to_solution(inst, partial)
