"""El modelo del CPMP escrito como piezas (`core.model_parts`), sin vista MIP: la referencia
contra la que se prueba el mecanismo y con la que se generan los casos (`cases.py`). En un
problema nuevo este módulo lo escribe el LLM (`python -m llm.cycle model --problem cpmp`); aquí
está a mano para tener un banco de prueba, como `examples/cvrp/model_parts.py`.

Formato neutral de respuesta (el de los casos): lista de movimientos [so, sd], mover el tope
de la pila so (índice desde 0) a la pila sd, en orden desde el layout inicial. Familias:
`movimiento` (movimientos inválidos: origen vacío, destino lleno u origen = destino; no se
aplican) y `orden` (contenedores mal puestos al final). Término del objetivo: `movimientos`.

Vista constructiva neutral (`core.model_parts.CONSTRUCTION_PARTS`): la parcial es el layout tras
los movimientos hechos; las acciones son todos los movimientos válidos que no vuelven a un layout
ya recorrido; el respaldo es una búsqueda best-first por mal puestos. No decide qué mover: eso
es del puntaje. Sin vista MIP.
"""

from __future__ import annotations

import heapq
from random import Random

from examples.cpmp.instance import CPMPInstance


# ---------------------------------------------------------------- vista heurística
def canonical(sol):
    return tuple((int(a), int(b)) for a, b in sol)


def _bad(stacks) -> int:
    total = 0
    for st in stacks:
        n = 1 if st else 0
        while n < len(st) and st[n] <= st[n - 1]:
            n += 1
        total += len(st) - n
    return total


def _replay(inst: CPMPInstance, sol):
    stacks, invalid = [list(s) for s in inst.stacks], 0
    for so, sd in sol:
        if not (0 <= so < inst.S and 0 <= sd < inst.S) or so == sd or not stacks[so] or len(stacks[sd]) >= inst.H:
            invalid += 1
            continue
        stacks[sd].append(stacks[so].pop())
    return stacks, invalid


def _search(inst: CPMPInstance, start, rng: Random, max_nodes: int = 200_000):
    """Best-first por mal puestos desde `start` (tupla de tuplas): movimientos hasta ordenar."""
    H = inst.H
    parent = {start: None}
    heap = [(_bad(start), 0, rng.random(), start)]
    while heap and len(parent) <= max_nodes:
        b, depth, _, state = heapq.heappop(heap)
        if b == 0:
            path = []
            while parent[state] is not None:
                state, m = parent[state]
                path.append(m)
            return path[::-1]
        for so, src in enumerate(state):
            if not src:
                continue
            for sd, dst in enumerate(state):
                if sd == so or len(dst) >= H:
                    continue
                nxt = list(state)
                nxt[so], nxt[sd] = src[:-1], dst + (src[-1],)
                nxt = tuple(nxt)
                if nxt not in parent:
                    parent[nxt] = (state, (so, sd))
                    heapq.heappush(heap, (_bad(nxt), depth + 1, rng.random(), nxt))
    return None


def trivial_solution(inst: CPMPInstance):
    path = _search(inst, tuple(tuple(s) for s in inst.stacks), Random(0))
    return canonical(path or [])


def random_solution(inst: CPMPInstance, rng: Random):
    stacks, moves = [list(s) for s in inst.stacks], []
    for _ in range(rng.randint(1, 2 * inst.N + 1)):
        opts = [(a, b) for a in range(inst.S) for b in range(inst.S) if a != b and stacks[a] and len(stacks[b]) < inst.H]
        if not opts:
            break
        a, b = opts[rng.randrange(len(opts))]
        stacks[b].append(stacks[a].pop())
        moves.append((a, b))
    return canonical(moves)


def from_answer(inst: CPMPInstance, answer):
    return canonical(answer)


def violations(inst: CPMPInstance, sol) -> dict[str, float]:
    stacks, invalid = _replay(inst, sol)
    return {"movimiento": float(invalid), "orden": float(_bad(stacks))}


def cost_terms(inst: CPMPInstance, sol) -> dict[str, float]:
    return {"movimientos": float(len(sol))}


# ---------------------------------------------------------------- vista constructiva
# La parcial es (pilas, movimientos, layouts ya recorridos); una acción es un movimiento (so, sd).
# Todos los movimientos válidos que no vuelven a un layout ya recorrido, con un tope de 4N + 10
# movimientos; el respaldo es la búsqueda best-first. No decide qué mover: eso es del puntaje.
def _after(stacks, so, sd):
    nxt = list(stacks)
    nxt[so], nxt[sd] = nxt[so][:-1], nxt[sd] + (nxt[so][-1],)
    return tuple(nxt)


def empty_partial(inst: CPMPInstance):
    stacks = tuple(tuple(s) for s in inst.stacks)
    return (stacks, (), frozenset({stacks}))


def candidates(inst: CPMPInstance, partial) -> list:
    stacks, moves, seen = partial
    if _bad(stacks) == 0 or len(moves) >= 4 * inst.N + 10:
        return []
    return [(so, sd) for so in range(inst.S) for sd in range(inst.S)
            if so != sd and stacks[so] and len(stacks[sd]) < inst.H and _after(stacks, so, sd) not in seen]


def apply_action(inst: CPMPInstance, partial, action):
    stacks, moves, seen = partial
    nxt = _after(stacks, *action)
    return (nxt, moves + (tuple(action),), seen | {nxt})


def is_complete(inst: CPMPInstance, partial) -> bool:
    return _bad(partial[0]) == 0


def to_solution(inst: CPMPInstance, partial):
    return canonical(partial[1])


def complete_partial(inst: CPMPInstance, partial, rng: Random):
    stacks, moves, _ = partial
    for start, prefix in ((stacks, moves), (tuple(tuple(s) for s in inst.stacks), ())):
        path = _search(inst, start, Random(rng.random()))
        if path is not None:
            return canonical(prefix + tuple(path))
    return canonical(moves)


def partial_lower_bound(inst: CPMPInstance, partial) -> float:
    return float(len(partial[1]) + _bad(partial[0]))  # cada mal puesto se mueve al menos una vez


def partial_key(inst: CPMPInstance, partial):
    return partial[0]
