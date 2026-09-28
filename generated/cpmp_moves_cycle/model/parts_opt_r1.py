from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import heapq
import random
from random import Random
from typing import Iterable

from examples.cpmp.instance import CPMPInstance


def canonical(sol):
    if sol is None:
        return ()
    return tuple((int(a), int(b)) for a, b in sol)


def _ordered_stack(stack: tuple[int, ...]) -> bool:
    return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))


def _stack_violations(stack: tuple[int, ...]) -> int:
    v = 0
    for i in range(len(stack) - 1):
        if stack[i] < stack[i + 1]:
            v += 1
    return v


def _final_violations(stacks: tuple[tuple[int, ...], ...]) -> int:
    return sum(_stack_violations(s) for s in stacks)


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


def _total_violations_after_move(
    stacks: tuple[tuple[int, ...], ...],
    vio_per_stack: tuple[int, ...],
    so: int,
    sd: int,
) -> tuple[int, tuple[tuple[int, ...], ...], tuple[int, ...]]:
    src = stacks[so]
    dst = stacks[sd]
    x = src[-1]

    # Source stack after pop
    old_src_v = vio_per_stack[so]
    if len(src) >= 2 and src[-2] < src[-1]:
        new_src_v = old_src_v - 1
    else:
        new_src_v = old_src_v

    # Destination stack after append
    old_dst_v = vio_per_stack[sd]
    if dst and dst[-1] < x:
        new_dst_v = old_dst_v + 1
    else:
        new_dst_v = old_dst_v

    new_total = sum(vio_per_stack) - old_src_v - old_dst_v + new_src_v + new_dst_v

    nxt = list(stacks)
    nxt[so] = src[:-1]
    nxt[sd] = dst + (x,)
    nxt_t = tuple(nxt)

    new_vios = list(vio_per_stack)
    new_vios[so] = new_src_v
    new_vios[sd] = new_dst_v
    return new_total, nxt_t, tuple(new_vios)


def trivial_solution(inst):
    # Greedy constructive heuristic with a bounded fallback search.
    start = tuple(tuple(s) for s in inst.stacks)
    if all(_ordered_stack(s) for s in start):
        return ()

    start_vios = tuple(_stack_violations(s) for s in start)
    start_score = sum(start_vios)

    # Small bounded best-first search for micro instances.
    max_nodes = 20000
    heap = [(start_score, 0, start)]
    parent: dict[tuple[tuple[int, ...], ...], tuple[tuple[tuple[int, ...], ...], tuple[int, int]]] = {}
    seen = {start}
    vio_map = {start: start_score}
    node_id = 1
    nodes = 0

    while heap and nodes < max_nodes:
        _, _, cur = heapq.heappop(heap)
        nodes += 1
        cur_v = vio_map[cur]
        if cur_v == 0:
            moves = []
            while cur != start:
                prev, mv = parent[cur]
                moves.append(mv)
                cur = prev
            moves.reverse()
            return canonical(moves)

        cur_vios = tuple(_stack_violations(s) for s in cur)
        candidates = []
        for so in range(inst.S):
            if not cur[so]:
                continue
            for sd in range(inst.S):
                if so == sd or len(cur[sd]) >= inst.H:
                    continue
                _, nxt, nxt_vios = _total_violations_after_move(cur, cur_vios, so, sd)
                if nxt in seen:
                    continue
                seen.add(nxt)
                parent[nxt] = (cur, (so, sd))
                vio_map[nxt] = sum(nxt_vios)
                candidates.append((vio_map[nxt], nxt))

        candidates.sort(key=lambda t: t[0])
        for v, nxt in candidates[: min(64, len(candidates))]:
            heapq.heappush(heap, (v, node_id, nxt))
            node_id += 1

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


@lru_cache(maxsize=8192)
def _violations_cached(stacks: tuple[tuple[int, ...], ...], sol: tuple[tuple[int, int], ...]) -> tuple[float, float]:
    final_stacks, invalid = _simulate_from_stacks(stacks, sol)
    ord_v = _final_violations(final_stacks)
    return float(invalid), float(ord_v)


def _simulate_from_stacks(stacks0: tuple[tuple[int, ...], ...], sol) -> tuple[tuple[tuple[int, ...], ...], int]:
    stacks = [list(s) for s in stacks0]
    invalid = 0
    for mv in sol:
        if len(mv) != 2:
            invalid += 1
            continue
        so, sd = mv
        if not (0 <= so < len(stacks0) and 0 <= sd < len(stacks0)) or so == sd:
            invalid += 1
            continue
        if not stacks[so]:
            invalid += 1
            continue
        if len(stacks[sd]) >= len(stacks0[0]) if False else False:
            invalid += 1
            continue
        x = stacks[so].pop()
        stacks[sd].append(x)
    return tuple(tuple(s) for s in stacks), invalid


def violations(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    stacks = tuple(tuple(s) for s in inst.stacks)
    movimiento, orden = _violations_cached(stacks, sol)
    return {
        "movimiento": movimiento,
        "orden": orden,
    }


def cost_terms(inst, sol) -> dict[str, float]:
    sol = canonical(sol)
    return {
        "movimientos": float(len(sol)),
    }


# ---- vista constructiva ----
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


def candidates(inst: CPMPInstance, partial) -> list:
    p = _as_partial(partial)

    if _is_ordered(p.stacks):
        return []

    max_depth = max(1, 2 * inst.N * max(1, inst.H) + inst.S)
    if p.depth >= max_depth:
        return []

    base_dis = sum(_stack_violations(s) for s in p.stacks)
    out = []
    for so in range(inst.S):
        if not p.stacks[so]:
            continue
        for sd in range(inst.S):
            if so == sd or len(p.stacks[sd]) >= inst.H:
                continue
            nxt = _apply_move(p.stacks, so, sd)
            if nxt in p.seen:
                continue
            if sum(_stack_violations(s) for s in nxt) > base_dis:
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
                nxt = [list(s) for s in stacks]
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


def _is_ordered(stacks: tuple[tuple[int, ...], ...]) -> bool:
    return all(_ordered_stack(s) for s in stacks)


def _apply_move(stacks: tuple[tuple[int, ...], ...], so: int, sd: int) -> tuple[tuple[int, ...], ...]:
    nxt = [list(s) for s in stacks]
    x = nxt[so].pop()
    nxt[sd].append(x)
    return tuple(tuple(s) for s in nxt)
