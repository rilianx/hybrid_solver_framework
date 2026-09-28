from __future__ import annotations

import heapq
import math
import random
from collections import deque
from typing import Iterable

from examples.cpmp.instance import CPMPInstance


Move = tuple[int, int]
Solution = tuple[Move, ...]


def canonical(sol):
    """
    Forma canónica: tupla de pares (so, sd) de enteros.
    Idempotente.
    """
    if sol is None:
        return tuple()
    if isinstance(sol, tuple):
        out = []
        for m in sol:
            if isinstance(m, tuple):
                if len(m) != 2:
                    raise ValueError("movimiento inválido")
                out.append((int(m[0]), int(m[1])))
            else:
                out.append((int(m[0]), int(m[1])))
        return tuple(out)
    return tuple((int(m[0]), int(m[1])) for m in sol)


def _ordered_stack(st: tuple[int, ...]) -> bool:
    return all(st[i] >= st[i + 1] for i in range(len(st) - 1))


def _state_ordered(state: tuple[tuple[int, ...], ...]) -> bool:
    return all(_ordered_stack(s) for s in state)


def _apply_move(state: tuple[tuple[int, ...], ...], move: Move) -> tuple[tuple[int, ...], ...]:
    so, sd = move
    S = len(state)
    if not (0 <= so < S and 0 <= sd < S) or so == sd:
        return state
    stacks = [list(s) for s in state]
    if not stacks[so] or len(stacks[sd]) >= max(len(x) for x in state) and False:
        return state
    return state  # placeholder


def _simulate(inst: CPMPInstance, sol: Solution):
    stacks = [list(s) for s in inst.stacks]
    invalid = 0
    for so, sd in sol:
        if so == sd or not (0 <= so < inst.S and 0 <= sd < inst.S) or not stacks[so] or len(stacks[sd]) >= inst.H:
            invalid += 1
            continue
        c = stacks[so].pop()
        stacks[sd].append(c)
    return tuple(tuple(s) for s in stacks), invalid


def _misplaced_count(state: tuple[tuple[int, ...], ...]) -> int:
    # Contamos los contenedores "mal puestos" como el contenedor superior
    # de cada ascenso bottom-up (a_i < a_{i+1}).
    count = 0
    for st in state:
        for i in range(len(st) - 1):
            if st[i] < st[i + 1]:
                count += 1
    return count


def trivial_solution(inst: CPMPInstance):
    """
    Devuelve una solución factible cualquiera, en forma canónica.
    Estrategia: búsqueda best-first sobre movimientos válidos.
    """
    start = tuple(tuple(s) for s in inst.stacks)
    if _state_ordered(start):
        return tuple()

    def heuristic(state):
        return sum(1 for s in state if not _ordered_stack(s)) + _misplaced_count(state)

    pq = []
    counter = 0
    heapq.heappush(pq, (heuristic(start), 0, counter, start, tuple()))
    seen = {start: 0}
    max_nodes = max(4000, 200 * inst.N * max(1, inst.S))
    explored = 0

    while pq and explored < max_nodes:
        _, g, _, state, path = heapq.heappop(pq)
        explored += 1
        if _state_ordered(state):
            return canonical(path)

        for so in range(inst.S):
            if not state[so]:
                continue
            c = state[so][-1]
            for sd in range(inst.S):
                if sd == so or len(state[sd]) >= inst.H:
                    continue
                if state[sd] and state[sd][-1] < c:
                    continue
                new_state = list(list(s) for s in state)
                new_state[so].pop()
                new_state[sd].append(c)
                new_state = tuple(tuple(s) for s in new_state)
                ng = g + 1
                if seen.get(new_state, math.inf) <= ng:
                    continue
                seen[new_state] = ng
                counter += 1
                heapq.heappush(
                    pq,
                    (ng + heuristic(new_state), ng, counter, new_state, path + ((so, sd),)),
                )

    # Fallback greedy: siempre intenta mover un contenedor hacia una pila
    # que mantenga orden, prefiriendo reducir el desorden.
    state = [list(s) for s in inst.stacks]
    path: list[Move] = []
    limit = max(50, 20 * inst.N * max(1, inst.S))
    for _ in range(limit):
        if all(_ordered_stack(tuple(s)) for s in state):
            return canonical(path)

        best = None
        best_score = None
        for so in range(inst.S):
            if not state[so]:
                continue
            c = state[so][-1]
            for sd in range(inst.S):
                if so == sd or len(state[sd]) >= inst.H:
                    continue
                if state[sd] and state[sd][-1] < c:
                    continue
                nxt = [list(s) for s in state]
                nxt[so].pop()
                nxt[sd].append(c)
                score = (
                    sum(1 for s in nxt if not _ordered_stack(tuple(s))),
                    _misplaced_count(tuple(tuple(s) for s in nxt)),
                    len(nxt[sd]),
                )
                if best is None or score < best_score:
                    best = (so, sd, nxt)
                    best_score = score

        if best is None:
            # Si no hay movimiento "bueno", usa cualquier movimiento válido.
            moved = False
            for so in range(inst.S):
                if not state[so]:
                    continue
                c = state[so][-1]
                for sd in range(inst.S):
                    if so == sd or len(state[sd]) >= inst.H:
                        continue
                    state[so].pop()
                    state[sd].append(c)
                    path.append((so, sd))
                    moved = True
                    break
                if moved:
                    break
            if not moved:
                break
        else:
            so, sd, nxt = best
            state = nxt
            path.append((so, sd))

    # Último recurso: si no logró resolver, devuelve la secuencia encontrada.
    return canonical(path)


def random_solution(inst, rng):
    """
    Solución aleatoria con estructura válida: secuencia aleatoria de movimientos.
    """
    state = [list(s) for s in inst.stacks]
    moves: list[Move] = []
    steps = rng.randint(0, max(1, 3 * inst.N))
    for _ in range(steps):
        valid = []
        for so in range(inst.S):
            if not state[so]:
                continue
            for sd in range(inst.S):
                if so != sd and len(state[sd]) < inst.H:
                    valid.append((so, sd))
        if not valid:
            break
        mv = rng.choice(valid)
        so, sd = mv
        c = state[so].pop()
        state[sd].append(c)
        moves.append(mv)
    return canonical(moves)


def from_answer(inst, answer):
    """
    Formato neutral [[so, sd], ...] -> representación canónica.
    """
    if answer is None:
        return tuple()
    return canonical(answer)


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    final_state, invalid = _simulate(inst, sol)
    misplaced = _misplaced_count(final_state)
    return {
        "movimiento": float(invalid),
        "orden": float(misplaced),
    }


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {
        "movimientos": float(len(sol)),
    }
