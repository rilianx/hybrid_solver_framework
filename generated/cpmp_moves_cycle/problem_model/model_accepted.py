from __future__ import annotations

from collections import deque
from functools import lru_cache
import random
from typing import Iterable

from examples.cpmp.instance import CPMPInstance


def canonical(sol):
    if sol is None:
        return ()
    return tuple((int(a), int(b)) for a, b in sol)


def _ordered_stack(stack: tuple[int, ...]) -> bool:
    return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))


def _final_violations(stacks: tuple[tuple[int, ...], ...]) -> int:
    v = 0
    for s in stacks:
        for i in range(len(s) - 1):
            if s[i] < s[i + 1]:
                v += 1
    return v


def _simulate(inst: CPMPInstance, sol) -> tuple[tuple[tuple[int, ...], ...], int]:
    stacks = [list(s) for s in inst.stacks]
    invalid = 0
    for mv in sol:
        if len(mv) != 2:
            invalid += 1
            continue
        so, sd = mv
        if not (0 <= so < inst.S and 0 <= sd < inst.S) or so == sd:
            invalid += 1
            continue
        if not stacks[so]:
            invalid += 1
            continue
        if len(stacks[sd]) >= inst.H:
            invalid += 1
            continue
        x = stacks[so].pop()
        stacks[sd].append(x)
    return tuple(tuple(s) for s in stacks), invalid


def trivial_solution(inst):
    # Greedy constructive heuristic with a bounded fallback search.
    start = tuple(tuple(s) for s in inst.stacks)
    if all(_ordered_stack(s) for s in start):
        return ()

    # Small bounded best-first search for micro instances.
    max_nodes = 20000
    q = deque([start])
    parent: dict[tuple[tuple[int, ...], ...], tuple[tuple[tuple[int, ...], ...], tuple[int, int]]] = {}
    seen = {start}
    nodes = 0

    def score(stacks: tuple[tuple[int, ...], ...]) -> tuple[int, int, int]:
        return (_final_violations(stacks), sum(len(s) for s in stacks), sum(len(s) for s in stacks))

    while q and nodes < max_nodes:
        # pop the current best among a small frontier window
        cur = min(q, key=score)
        q.remove(cur)
        nodes += 1
        if all(_ordered_stack(s) for s in cur):
            # reconstruct
            moves = []
            while cur != start:
                prev, mv = parent[cur]
                moves.append(mv)
                cur = prev
            moves.reverse()
            return canonical(moves)

        # generate valid moves, prefer improving ones
        cur_score = score(cur)
        candidates = []
        for so in range(inst.S):
            if not cur[so]:
                continue
            for sd in range(inst.S):
                if so == sd or len(cur[sd]) >= inst.H:
                    continue
                nxt = [list(s) for s in cur]
                x = nxt[so].pop()
                nxt[sd].append(x)
                nxt = tuple(tuple(s) for s in nxt)
                if nxt in seen:
                    continue
                seen.add(nxt)
                parent[nxt] = (cur, (so, sd))
                candidates.append((score(nxt), nxt))
        candidates.sort(key=lambda t: t[0])
        for _, nxt in candidates[: min(64, len(candidates))]:
            q.append(nxt)

    # Fallback greedy: always perform a valid move that most reduces disorder.
    stacks = [list(s) for s in inst.stacks]
    moves: list[tuple[int, int]] = []
    limit = 10 * inst.N * max(1, inst.H) + 100

    def disorder(sts: list[list[int]]) -> int:
        return sum(1 for s in sts for i in range(len(s) - 1) if s[i] < s[i + 1])

    for _ in range(limit):
        if all(_ordered_stack(tuple(s)) for s in stacks):
            return canonical(moves)

        base = disorder(stacks)
        best = None
        best_key = None
        for so in range(inst.S):
            if not stacks[so]:
                continue
            x = stacks[so][-1]
            for sd in range(inst.S):
                if so == sd or len(stacks[sd]) >= inst.H:
                    continue
                ok = (not stacks[sd]) or stacks[sd][-1] >= x
                nxt = [list(s) for s in stacks]
                nxt[so].pop()
                nxt[sd].append(x)
                d = disorder(nxt)
                key = (0 if ok else 1, d, len(moves))
                if best is None or key < best_key:
                    best = (so, sd, nxt)
                    best_key = key
        if best is None:
            break
        so, sd, nxt = best
        stacks = nxt
        moves.append((so, sd))

    return canonical(moves)


def random_solution(inst, rng):
    m = rng.randint(0, max(0, 3 * inst.N))
    sol = []
    for _ in range(m):
        so = rng.randrange(inst.S)
        sd = rng.randrange(inst.S)
        while sd == so:
            sd = rng.randrange(inst.S)
        sol.append((so, sd))
    return canonical(sol)


def from_answer(inst, answer):
    return canonical(answer)


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    final_stacks, invalid = _simulate(inst, sol)
    ord_v = _final_violations(final_stacks)
    return {
        "movimiento": float(invalid),
        "orden": float(ord_v),
    }


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {
        "movimientos": float(len(sol)),
    }
