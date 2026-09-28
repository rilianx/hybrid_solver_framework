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


# ---- vista constructiva ----
from typing import Any

from examples.cpmp.instance import CPMPInstance
from collections import deque


def _ordered_stack(stack: tuple[int, ...]) -> bool:
    return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))


def _ordered_layout(stacks: tuple[tuple[int, ...], ...]) -> bool:
    return all(_ordered_stack(s) for s in stacks)


def _apply_move(stacks: tuple[tuple[int, ...], ...], so: int, sd: int) -> tuple[tuple[int, ...], ...] | None:
    if so == sd:
        return None
    if not (0 <= so < len(stacks) and 0 <= sd < len(stacks)):
        return None
    if not stacks[so]:
        return None
    if len(stacks[sd]) >= len(stacks[sd]) + 1:  # placeholder, overwritten below
        return None
    # capacity check is done outside because we only know H via the instance
    lst = [list(s) for s in stacks]
    x = lst[so].pop()
    lst[sd].append(x)
    return tuple(tuple(s) for s in lst)


def _simulate_move(inst: CPMPInstance, stacks: tuple[tuple[int, ...], ...], action: tuple[int, int]) -> tuple[tuple[int, ...], ...] | None:
    so, sd = action
    if so == sd:
        return None
    if not (0 <= so < inst.S and 0 <= sd < inst.S):
        return None
    if not stacks[so]:
        return None
    if len(stacks[sd]) >= inst.H:
        return None
    lst = [list(s) for s in stacks]
    x = lst[so].pop()
    lst[sd].append(x)
    return tuple(tuple(s) for s in lst)


def empty_partial(inst):
    stacks = tuple(tuple(s) for s in inst.stacks)
    return {
        "stacks": stacks,
        "moves": (),
        "visited": frozenset({stacks}),
    }


def candidates(inst, partial) -> list:
    stacks = partial["stacks"]
    visited = partial["visited"]
    best = None
    best_score = None

    for so in range(inst.S):
        if not stacks[so]:
            continue
        x = stacks[so][-1]
        for sd in range(inst.S):
            if so == sd or len(stacks[sd]) >= inst.H:
                continue
            nxt = _simulate_move(inst, stacks, (so, sd))
            if nxt is None or nxt in visited:
                continue

            # Prefer moves that reduce disorder and keep the destination compatible.
            before = sum(1 for s in stacks for i in range(len(s) - 1) if s[i] < s[i + 1])
            after = sum(1 for s in nxt for i in range(len(s) - 1) if s[i] < s[i + 1])
            compatible = 0 if (not stacks[sd] or stacks[sd][-1] >= x) else 1
            score = (after - before, compatible, len(nxt[sd]), sd, so)

            if best is None or score < best_score:
                best = (so, sd)
                best_score = score

    return [best] if best is not None else []


def apply_action(inst, partial, action):
    stacks = partial["stacks"]
    nxt = _simulate_move(inst, stacks, action)
    if nxt is None:
        return {
            "stacks": stacks,
            "moves": partial["moves"],
            "visited": partial["visited"],
        }
    return {
        "stacks": nxt,
        "moves": partial["moves"] + (tuple(action),),
        "visited": partial["visited"] | {nxt},
    }


def is_complete(inst, partial) -> bool:
    return _ordered_layout(partial["stacks"])


def to_solution(inst, partial):
    return tuple((int(a), int(b)) for a, b in partial["moves"])


def complete_partial(inst, partial, rng):
    start = partial["stacks"]
    if _ordered_layout(start):
        return tuple((int(a), int(b)) for a, b in partial["moves"])

    q = deque([start])
    parent: dict[tuple[tuple[int, ...], ...], tuple[tuple[tuple[int, ...], ...], tuple[int, int]]] = {}
    seen = {start}
    limit = 50000
    explored = 0

    while q and explored < limit:
        cur = q.popleft()
        explored += 1
        if _ordered_layout(cur):
            rev = []
            while cur != start:
                prev, mv = parent[cur]
                rev.append(mv)
                cur = prev
            rev.reverse()
            return tuple((int(a), int(b)) for a, b in partial["moves"] + tuple(rev))

        for so in range(inst.S):
            if not cur[so]:
                continue
            for sd in range(inst.S):
                if so == sd or len(cur[sd]) >= inst.H:
                    continue
                nxt = _simulate_move(inst, cur, (so, sd))
                if nxt is None or nxt in seen:
                    continue
                seen.add(nxt)
                parent[nxt] = (cur, (so, sd))
                q.append(nxt)

    # Greedy fallback: always take the best valid move until ordered or capped.
    stacks = [list(s) for s in start]
    moves = list(partial["moves"])
    cap = 10 * max(1, inst.N) * max(1, inst.H) + 100

    def disorder(sts):
        return sum(1 for s in sts for i in range(len(s) - 1) if s[i] < s[i + 1])

    for _ in range(cap):
        if all(_ordered_stack(tuple(s)) for s in stacks):
            return tuple((int(a), int(b)) for a, b in moves)

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
                if stacks[sd] and stacks[sd][-1] < x:
                    continue
                nxt = [list(s) for s in stacks]
                nxt[so].pop()
                nxt[sd].append(x)
                key = (disorder(nxt), len(nxt[sd]), sd, so)
                if best is None or key < best_key:
                    best = nxt
                    best_key = key
                    best_move = (so, sd)
        if best is None:
            break
        stacks = best
        moves.append(best_move)

    return tuple((int(a), int(b)) for a, b in moves)


def partial_lower_bound(inst, partial) -> float:
    # At least the number of moves already committed.
    return float(len(partial["moves"]))


def partial_key(inst, partial):
    return partial["stacks"]
