"""Oráculo exacto del CPMP: la distancia (movimientos mínimos) de un layout al ordenado.

A* sobre layouts con h = mal puestos (admisible: cada mal puesto se mueve al menos una vez).
Alcanza en 5×5 (≈ 0,5 s desde el layout inicial) y no en 6×6: con `budget` nodos agotados
devuelve None y quien lo usa sigue sin oráculo en esa instancia.

Para `evolve` (`ProblemPack.oracle_distance`): con d(·), cada decisión del greedy tiene un
arrepentimiento exacto, regret(a) = 1 + d(s') − d(s) ≥ 0, y su suma a lo largo de la
construcción es movimientos − óptimo. Es la asignación de culpa exacta por estado de la máquina
y da contraejemplos (dónde se aparta del óptimo y qué haría el óptimo).

Caché acotada: cada búsqueda que llega al objetivo deja también la distancia de los estados de
su camino óptimo (d(sᵢ) = d − i), que son los que el greedy suele pisar después.
"""

from __future__ import annotations

import heapq

from .construction import _bad

CACHE_MAX = 200_000
_cache: dict = {}


def _remember(state, d) -> None:
    if len(_cache) >= CACHE_MAX:
        _cache.clear()
    _cache[state] = d


def optimal_distance(state: tuple, H: int, budget: int = 400_000) -> int | None:
    """Movimientos mínimos para ordenar `state` (tupla de pilas); None si agota `budget` nodos."""
    if state in _cache:
        return _cache[state]
    g = {state: 0}
    parent: dict = {state: None}
    heap = [(_bad(state), 0, state)]
    expanded = 0
    while heap:
        _, d, s = heapq.heappop(heap)
        if d > g.get(s, 1 << 30):
            continue
        if _bad(s) == 0:
            path = [s]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            for i, x in enumerate(reversed(path)):  # del inicio al objetivo: d(x) = d − i
                _remember(x, d - i)
            return d
        expanded += 1
        if expanded > budget:
            return None
        for so, src in enumerate(s):
            if not src:
                continue
            for sd, dst in enumerate(s):
                if sd == so or len(dst) >= H:
                    continue
                nxt = list(s)
                nxt[so], nxt[sd] = src[:-1], dst + (src[-1],)
                nxt = tuple(nxt)
                nd = d + 1
                if nd < g.get(nxt, 1 << 30):
                    g[nxt] = nd
                    parent[nxt] = s
                    heapq.heappush(heap, (nd + _bad(nxt), nd, nxt))
    return None


MAX_CELLS = 25  # S·H: hasta 5×5; en 6×6 la búsqueda no termina y rendirse cuesta segundos por llamada


def oracle_distance(inst, partial) -> int | None:
    """Para `ProblemPack.oracle_distance`: el parcial es un `Layout`. None fuera de su alcance."""
    if inst.S * inst.H > MAX_CELLS:
        return None
    return optimal_distance(partial.state(), inst.H)


__all__ = ["optimal_distance", "oracle_distance"]
