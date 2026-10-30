"""Componentes del job shop escritos a mano (representación por secuencias): el catálogo de referencia.

- `JobOrder` (constructor): todas las máquinas en el orden de los trabajos. Siempre factible y mala.
- Puntajes del despacho (`greedy_score`): `EarliestEnd` (la operación que antes termina) y
  `MostWorkRemaining` (entre las que pueden empezar antes, la del trabajo con más trabajo pendiente).
- `CriticalSwap` (N5, Nowicki y Smutnicki 1996): intercambiar las dos primeras o las dos últimas
  operaciones de cada bloque del camino crítico. Nunca forma un ciclo.
- `CriticalInsert`: mover una operación de un bloque crítico al principio o al final del bloque.
- `CriticalKick` (perturbación): `strength` intercambios adyacentes al azar en el camino crítico.
- `TimeWindowRemoval` y `MachineRemoval` (destrucción): liberan el orden entre las operaciones de una
  ventana de tiempo, o el de algunas máquinas, para que el sub-MIP las reordene.

Los movimientos se describen por máquina y trabajos (la forma canónica no reordena las máquinas).
"""

from __future__ import annotations

from random import Random

from .model_parts import _y, canonical, critical_blocks, critical_path, jobs_on, schedule


class JobOrder:
    def build(self, inst, rng: Random):
        return canonical(jobs_on(inst, m) for m in inst.machines)


class EarliestEnd:
    def __init__(self, problem):
        pass

    def score(self, partial, action) -> float:
        return action.end + 1e-3 * action.start


class MostWorkRemaining:
    def __init__(self, problem):
        inst = problem.inst
        self.rest = [[sum(p for _, p in r[k:]) for k in range(len(r))] for r in inst.routes]
        self.scale = 1.0 + inst.horizon()

    def score(self, partial, action) -> float:
        return action.start - self.rest[action.job][action.op] / self.scale


def _swap(sol, m, a, b):
    seqs = [list(s) for s in sol]
    i, j = seqs[m].index(a), seqs[m].index(b)
    seqs[m][i], seqs[m][j] = seqs[m][j], seqs[m][i]
    return canonical(seqs)


class CriticalSwap:
    def __init__(self, problem):
        self.problem, self.inst = problem, problem.inst

    def moves(self, sol):
        seen = set()
        for m, block in critical_blocks(self.inst, sol):
            for a, b in {(block[0], block[1]), (block[-2], block[-1])}:
                if (m, a, b) not in seen:
                    seen.add((m, a, b))
                    yield (m, a, b)

    def apply(self, sol, mv):
        return _swap(sol, *mv)

    def undo(self, sol, mv):
        return _swap(sol, *mv)

    def inverse(self, mv):  # para la memoria tabú: el intercambio que lo deshace
        m, a, b = mv
        return (m, b, a)

    def delta(self, sol, mv):
        return self.problem.objective(self.apply(sol, mv)) - self.problem.objective(sol)


def _move(sol, m, job, to):
    seqs = [list(s) for s in sol]
    seqs[m].remove(job)
    seqs[m].insert(to, job)
    return canonical(seqs)


class CriticalInsert:
    """Mover un trabajo de un bloque crítico al principio o al final del bloque. Movimiento
    `(máquina, trabajo, posición de origen, posición de destino)`."""

    def __init__(self, problem):
        self.problem, self.inst = problem, problem.inst

    def moves(self, sol):
        for m, block in critical_blocks(self.inst, sol):
            first = sol[m].index(block[0])
            last = first + len(block) - 1
            for i in range(first, last + 1):
                for to in {first, last} - {i}:
                    if abs(to - i) > 1:  # los adyacentes ya son intercambios
                        yield (m, sol[m][i], i, to)

    def apply(self, sol, mv):
        m, job, _, to = mv
        return _move(sol, m, job, to)

    def undo(self, sol, mv):
        m, job, frm, _ = mv
        return _move(sol, m, job, frm)

    def inverse(self, mv):
        m, job, frm, to = mv
        return (m, job, to, frm)

    def delta(self, sol, mv):
        return self.problem.objective(self.apply(sol, mv)) - self.problem.objective(sol)


class CriticalKick:
    def __init__(self, problem):
        self.inst = problem.inst

    def perturb(self, sol, strength, rng: Random):
        for _ in range(max(1, int(round(strength)))):
            path = critical_path(self.inst, sol)
            pairs = [(self.inst.machine(*a), a[0], b[0]) for a, b in zip(path, path[1:])
                     if self.inst.machine(*a) == self.inst.machine(*b)]
            if not pairs:
                break
            sol = _swap(sol, *rng.choice(pairs))
        return sol


def _free_pairs(problem, sol, ops: set[tuple[int, int]]):
    """Libera el orden, en cada máquina, entre las operaciones `ops` (j, m); fija el resto."""
    inst = problem.inst
    free = {_y(m, i, j) for m in inst.machines for i in jobs_on(inst, m) for j in jobs_on(inst, m)
            if i != j and (i, m) in ops and (j, m) in ops}
    assignment = problem.to_assignment(sol)
    return {v: val for v, val in assignment.items() if v not in free}, free


class TimeWindowRemoval:
    """Las operaciones que empiezan en una ventana de tiempo al azar (una fracción `ratio` de todas)."""

    def __init__(self, problem):
        self.problem = problem

    def destroy(self, sol, ratio, rng: Random):
        inst = self.problem.inst
        start = schedule(inst, sol)[0]
        ops = sorted((start[j][k], j, inst.machine(j, k)) for j in inst.jobs for k in range(len(inst.routes[j])))
        size = max(2, int(round(ratio * len(ops))))
        first = rng.randrange(max(1, len(ops) - size + 1))
        return _free_pairs(self.problem, sol, {(j, m) for _, j, m in ops[first:first + size]})


class MachineRemoval:
    """El orden completo de algunas máquinas al azar (una fracción `ratio`, al menos una)."""

    def __init__(self, problem):
        self.problem = problem

    def destroy(self, sol, ratio, rng: Random):
        inst = self.problem.inst
        ms = rng.sample(list(inst.machines), max(1, int(round(ratio * inst.n_machines))))
        return _free_pairs(self.problem, sol, {(j, m) for m in ms for j in jobs_on(inst, m)})
