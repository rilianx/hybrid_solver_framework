"""El modelo del CPMP escrito como piezas (`core.model_parts`), sin vista MIP: la referencia
contra la que se prueba el mecanismo y con la que se generan los casos (`cases.py`). En un
problema nuevo este módulo lo escribe el LLM (`python -m examples.cpmp.generate_model`); aquí
está a mano para tener un banco de prueba, como `examples/cvrp/model_parts.py`.

Formato neutral de respuesta (el de los casos): lista de movimientos [so, sd], mover el tope
de la pila so (índice desde 0) a la pila sd, en orden desde el layout inicial. Familias:
`movimiento` (movimientos inválidos: origen vacío, destino lleno u origen = destino; no se
aplican) y `orden` (contenedores mal puestos al final). Término del objetivo: `movimientos`.

Vista constructiva neutral: el parcial es el layout tras los movimientos hechos; las acciones
son todos los movimientos válidos que no vuelven a un layout ya recorrido; el respaldo es una
búsqueda best-first por mal puestos. No decide qué mover: eso es del puntaje.
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
class Partial:
    """Layout tras `moves`. Lo lee un puntaje: stacks (tuplas de grupos, abajo → arriba), H, G,
    moves, h(i), e(i), g(i) (grupo del tope; una pila vacía vale G), is_sorted_stack(i),
    bad() (mal puestos)."""

    __slots__ = ("stacks", "H", "G", "moves", "seen")

    def __init__(self, stacks, H, G, moves=(), seen=frozenset()):
        self.stacks, self.H, self.G, self.moves = tuple(stacks), H, G, tuple(moves)
        self.seen = seen | {self.stacks}

    def h(self, i):
        return len(self.stacks[i])

    def e(self, i):
        return self.H - len(self.stacks[i])

    def g(self, i):
        return self.stacks[i][-1] if self.stacks[i] else self.G

    def is_sorted_stack(self, i):
        s = self.stacks[i]
        return all(s[k] >= s[k + 1] for k in range(len(s) - 1))

    def bad(self):
        return _bad(self.stacks)


class _View:
    def __init__(self, inst: CPMPInstance):
        self.inst = inst
        self.max_moves = 4 * inst.N + 10

    def empty(self):
        return Partial(self.inst.stacks, self.inst.H, self.inst.G)

    def _after(self, p, so, sd):
        nxt = list(p.stacks)
        nxt[so], nxt[sd] = nxt[so][:-1], nxt[sd] + (nxt[so][-1],)
        return tuple(nxt)

    def candidates(self, p):
        if p.bad() == 0 or len(p.moves) >= self.max_moves:
            return []
        return [(so, sd) for so in range(len(p.stacks)) for sd in range(len(p.stacks))
                if so != sd and p.stacks[so] and len(p.stacks[sd]) < p.H and self._after(p, so, sd) not in p.seen]

    def apply(self, p, a):
        so, sd = a
        return Partial(self._after(p, so, sd), p.H, p.G, p.moves + ((so, sd),), p.seen)

    def is_complete(self, p):
        return p.bad() == 0

    def to_solution(self, p):
        return canonical(p.moves)

    def complete(self, p, rng):
        for start, prefix in ((p.stacks, p.moves), (tuple(self.inst.stacks), ())):
            path = _search(self.inst, start, Random(rng.random()))
            if path is not None:
                return canonical(prefix + tuple(path))
        return canonical(p.moves)

    def lower_bound(self, p):
        return len(p.moves) + p.bad()

    def key(self, p):
        return p.stacks


def construction_view(inst: CPMPInstance):
    return _View(inst)
