from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from random import Random
from typing import Any

from examples.cpmp.instance import CPMPInstance


def _inst_key(inst: CPMPInstance) -> tuple:
    return (
        inst.S,
        inst.H,
        tuple(tuple(s) for s in inst.stacks),
        getattr(inst, "name", None),
    )


def canonical(sol):
    if sol is None:
        return ()
    return tuple((int(a), int(b)) for a, b in sol)


@lru_cache(maxsize=8192)
def _ordered_stack_cached(stack: tuple[int, ...]) -> bool:
    return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))


def _ordered_stack(stack: tuple[int, ...]) -> bool:
    return _ordered_stack_cached(stack)


@lru_cache(maxsize=8192)
def _final_violations_cached(stacks: tuple[tuple[int, ...], ...]) -> int:
    v = 0
    for s in stacks:
        for i in range(len(s) - 1):
            if s[i] < s[i + 1]:
                v += 1
    return v


def _final_violations(stacks: tuple[tuple[int, ...], ...]) -> int:
    return _final_violations_cached(stacks)


@lru_cache(maxsize=8192)
def _simulate_cached(inst_key: tuple, sol: tuple[tuple[int, int], ...]) -> tuple[tuple[tuple[int, ...], ...], int]:
    S, H, start_stacks, _name = inst_key
    stacks = [list(s) for s in start_stacks]
    invalid = 0
    for so, sd in sol:
        if not (0 <= so < S and 0 <= sd < S) or so == sd:
            invalid += 1
            continue
        if not stacks[so]:
            invalid += 1
            continue
        if len(stacks[sd]) >= H:
            invalid += 1
            continue
        x = stacks[so].pop()
        stacks[sd].append(x)
    return tuple(tuple(s) for s in stacks), invalid


def _simulate(inst: CPMPInstance, sol) -> tuple[tuple[tuple[int, ...], ...], int]:
    return _simulate_cached(_inst_key(inst), canonical(sol))


def trivial_solution(inst):
    start = tuple(tuple(s) for s in inst.stacks)
    if all(_ordered_stack(s) for s in start):
        return ()

    max_nodes = 20000
    q = deque([start])
    parent: dict[tuple[tuple[int, ...], ...], tuple[tuple[tuple[int, ...], ...], tuple[int, int]]] = {}
    seen = {start}
    nodes = 0

    def score(stacks: tuple[tuple[int, ...], ...]) -> tuple[int, int, int]:
        v = _final_violations(stacks)
        n = sum(len(s) for s in stacks)
        return (v, n, n)

    while q and nodes < max_nodes:
        cur = min(q, key=score)
        q.remove(cur)
        nodes += 1
        if all(_ordered_stack(s) for s in cur):
            moves = []
            while cur != start:
                prev, mv = parent[cur]
                moves.append(mv)
                cur = prev
            moves.reverse()
            return canonical(moves)

        candidates = []
        cur_lists = [list(s) for s in cur]
        for so in range(inst.S):
            if not cur_lists[so]:
                continue
            for sd in range(inst.S):
                if so == sd or len(cur_lists[sd]) >= inst.H:
                    continue
                nxt = [lst[:] for lst in cur_lists]
                nxt[so].pop()
                nxt[sd].append(cur_lists[so][-1])
                nxtt = tuple(tuple(s) for s in nxt)
                if nxtt in seen:
                    continue
                seen.add(nxtt)
                parent[nxtt] = (cur, (so, sd))
                candidates.append((score(nxtt), nxtt))
        candidates.sort(key=lambda t: t[0])
        for _, nxt in candidates[: min(64, len(candidates))]:
            q.append(nxt)

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
                nxt = [lst[:] for lst in stacks]
                nxt[so].pop()
                nxt[sd].append(x)
                d = disorder(nxt)
                key = (0 if (not nxt[sd][:-1] or nxt[sd][-2] >= x) else 1, d, len(moves))
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


@lru_cache(maxsize=8192)
def _violations_cached(inst_key: tuple, sol: tuple[tuple[int, int], ...]) -> tuple[float, float]:
    S, H, start_stacks, _name = inst_key
    stacks, invalid = _simulate_cached(inst_key, sol)
    ord_v = _final_violations_cached(stacks)
    return float(invalid), float(ord_v)


def violations(inst, sol) -> dict[str, float]:
    inv, ord_v = _violations_cached(_inst_key(inst), canonical(sol))
    return {"movimiento": inv, "orden": ord_v}


@lru_cache(maxsize=8192)
def _cost_terms_cached(sol: tuple[tuple[int, int], ...]) -> float:
    return float(len(sol))


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {"movimientos": _cost_terms_cached(sol)}


@dataclass(frozen=True)
class CPMPPartial:
    stacks: tuple[tuple[int, ...], ...]
    moves: tuple[tuple[int, int], ...]
    seen: frozenset[tuple[tuple[int, ...], ...]]
    depth: int = 0


def empty_partial(inst: CPMPInstance):
    stacks = tuple(tuple(s) for s in inst.stacks)
    return CPMPPartial(stacks=stacks, moves=(), seen=frozenset({stacks}), depth=0)


def _as_partial(partial) -> CPMPPartial:
    if isinstance(partial, CPMPPartial):
        return partial
    stacks = tuple(tuple(s) for s in partial.stacks)  # type: ignore[attr-defined]
    moves = tuple(getattr(partial, "moves", ()))
    seen = getattr(partial, "seen", None)
    if seen is None:
        seen = {stacks}
    depth = int(getattr(partial, "depth", len(moves)))
    return CPMPPartial(stacks=stacks, moves=moves, seen=frozenset(seen), depth=depth)


def _is_ordered(stacks: tuple[tuple[int, ...], ...]) -> bool:
    return all(_ordered_stack(s) for s in stacks)


def _apply_move(stacks: tuple[tuple[int, ...], ...], so: int, sd: int) -> tuple[tuple[int, ...], ...]:
    nxt = [list(s) for s in stacks]
    x = nxt[so].pop()
    nxt[sd].append(x)
    return tuple(tuple(s) for s in nxt)


def candidates(inst: CPMPInstance, partial) -> list:
    p = _as_partial(partial)
    if _is_ordered(p.stacks):
        return []
    max_depth = max(1, 2 * inst.N * max(1, inst.H) + inst.S)
    if p.depth >= max_depth:
        return []

    base_dis = _final_violations(p.stacks)
    out = []
    S, H = inst.S, inst.H
    stacks = p.stacks
    seen = p.seen
    for so in range(S):
        if not stacks[so]:
            continue
        for sd in range(S):
            if so == sd or len(stacks[sd]) >= H:
                continue
            nxt = _apply_move(stacks, so, sd)
            if nxt in seen:
                continue
            if _final_violations(nxt) > base_dis:
                continue
            out.append((so, sd))
    return out


def apply_action(inst: CPMPInstance, partial, action):
    p = _as_partial(partial)
    so, sd = action
    nxt = _apply_move(p.stacks, so, sd)
    return CPMPPartial(
        stacks=nxt,
        moves=p.moves + ((int(so), int(sd)),),
        seen=frozenset(set(p.seen) | {nxt}),
        depth=p.depth + 1,
    )


def is_complete(inst: CPMPInstance, partial) -> bool:
    p = _as_partial(partial)
    return _is_ordered(p.stacks)


def to_solution(inst: CPMPInstance, partial):
    p = _as_partial(partial)
    return canonical(p.moves)


def complete_partial(inst: CPMPInstance, partial, rng: Random):
    p = _as_partial(partial)

    if _is_ordered(p.stacks):
        return canonical(p.moves)

    tmp = CPMPInstance(tuple(tuple(s) for s in p.stacks), inst.H, name=inst.name)
    tail = trivial_solution(tmp)
    final_stacks, invalid = _simulate(tmp, tail)
    if invalid == 0 and _is_ordered(final_stacks):
        return canonical(p.moves + canonical(tail))

    stacks = [list(s) for s in p.stacks]
    moves = list(p.moves)
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
                nxt = [lst[:] for lst in stacks]
                nxt[so].pop()
                nxt[sd].append(x)
                d = disorder(nxt)
                if d > base:
                    continue
                ok = (not stacks[sd]) or stacks[sd][-1] >= x
                key = (0 if ok else 1, d, so, sd)
                if best is None or key < best_key:
                    best = (so, sd, nxt)
                    best_key = key
        if best is None:
            break
        so, sd, nxt = best
        stacks = nxt
        moves.append((so, sd))

    tmp = CPMPInstance(tuple(tuple(s) for s in stacks), inst.H, name=inst.name)
    tail = trivial_solution(tmp)
    return canonical(moves + canonical(tail))


def partial_lower_bound(inst: CPMPInstance, partial) -> float:
    p = _as_partial(partial)
    return float(sum(1 for s in p.stacks for i in range(len(s) - 1) if s[i] < s[i + 1]))


def partial_key(inst: CPMPInstance, partial):
    p = _as_partial(partial)
    return p.stacks
