"""Vista constructiva del CPMP (`core.contracts.ConstructionView`) y componentes de referencia.

La vista es neutral: solo sabe del problema, no de ninguna heurística.

- Estado parcial: el `Layout` (pilas, movimientos hechos, layouts ya recorridos).
- Acción: `Move(so, sd)`, mover el tope de la pila so a la sd. Candidatos: todos los
  movimientos válidos que no vuelven a un layout ya recorrido en esta construcción; así un
  puntaje malo no puede ciclar, solo alargar la solución.
- Completo: el layout está ordenado. A partir de `max_moves` movimientos no hay candidatos.
- `complete` (respaldo): búsqueda best-first genérica sobre layouts (menos mal puestos
  primero, sin repetir layouts; `best_first`), sin reglas de ninguna heurística publicada.
  No garantiza calidad, y en instancias grandes se agota (5×7 y 10×10 al estilo CVS con
  20 mil nodos): ahí la construcción queda infactible, sin ningún último recurso más fuerte.
- `lower_bound` = movimientos hechos + mal puestos (cada uno se mueve al menos una vez);
  `key` = el layout, para que la beam search descarte repetidos.

Lo que decide cómo construir es el puntaje (slot `greedy_score`), escrito a mano o generado
por el LLM, y la estrategia que lo usa (`GreedyConstructor`, `BeamSearchConstructor`). De
referencia, a mano:

- `FRGPolicy`: FRG (Araya y Toledo 2023) como política con memoria (slot
  `construction_policy`): 0 para el movimiento que haría FRG, 1 para el resto. El greedy con
  esta política es FRG; como rollout de la beam search da BS-FRG.
- `DestinationRank`: la regla `select_destination` del mismo paper, miope (sin reducciones).
- `FRGConstructor`: FRG completo, con la asignación de la §4.3.2 como respaldo.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from .frg import DEFAULT, FRGConfig, FRGState, destination_rank, frg, frg_step
from .layout import Layout

if TYPE_CHECKING:
    from .instance import CPMPInstance


@dataclass(frozen=True)
class Move:
    """Mover el contenedor del tope de la pila `so` a la pila `sd`."""

    so: int
    sd: int


def _bad(stacks) -> int:
    total = 0
    for st in stacks:
        n = 1 if st else 0
        while n < len(st) and st[n] <= st[n - 1]:
            n += 1
        total += len(st) - n
    return total


def best_first(L: Layout, rng: Random, max_nodes: int = 200_000) -> list[tuple[int, int]] | None:
    """Búsqueda best-first desde L: expande primero el layout con menos mal puestos (empates:
    menos movimientos, después al azar), sin repetir layouts. Devuelve los movimientos que
    faltan para ordenar, o None si agota `max_nodes`. Es completa en un espacio finito: si
    hay solución y alcanza el presupuesto, la encuentra."""
    import heapq

    H = L.H
    start = L.state()
    parent: dict = {start: None}
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


def _extend(L: Layout, moves) -> Layout:
    q = L.copy(track=False)
    for m in moves:
        q.move(*m)
    return q


class CPMPConstructionView:
    def __init__(self, problem, inst: "CPMPInstance", max_moves: int | None = None, fallback_nodes: int = 20_000):
        self.problem, self.inst = problem, inst
        self.max_moves = max_moves
        self.fallback_nodes = fallback_nodes
        self.failures = 0

    def _limit(self, L: Layout) -> int:
        """Por defecto 4N + 10: FRG usa 1,3–1,6 N en las instancias al estilo CVS; un puntaje
        que se pasa de eso está vagando y conviene cerrar con el respaldo."""
        return 4 * L.N + 10 if self.max_moves is None else self.max_moves

    def empty(self) -> Layout:
        return Layout.from_instance(self.inst, track=True)

    def candidates(self, L: Layout):
        if L.is_sorted() or len(L.moves) >= self._limit(L):
            return []
        seen = L.visited or set()
        return [Move(so, sd) for so in range(L.S) for sd in range(L.S)
                if L.valid(so, sd) and L.after(so, sd) not in seen]

    def apply(self, L: Layout, a: Move) -> Layout:
        q = L.copy()
        q.move(a.so, a.sd)
        return q

    def is_complete(self, L: Layout) -> bool:
        return L.is_sorted()

    def to_solution(self, L: Layout):
        from .problem_model import CPMPSolution

        return CPMPSolution(tuple(L.moves))

    def complete(self, L: Layout, rng: Random):
        """Best-first desde el parcial y, si agota `fallback_nodes`, desde el layout inicial.
        Si tampoco encuentra, devuelve el parcial tal cual (infactible: el validador lo
        rechaza y el tuner lo penaliza). No hay un último recurso más fuerte a propósito: si
        lo hubiera, un puntaje malo heredaría su calidad en las instancias grandes."""
        for start in (L, self.empty()):
            rest = best_first(start, Random(rng.random()), self.fallback_nodes)
            if rest is not None:
                return self.to_solution(_extend(start, rest))
        self.failures += 1
        return self.to_solution(L)

    def lower_bound(self, L: Layout) -> int:
        return len(L.moves) + L.bad()

    def key(self, L: Layout):
        return L.state()


# --- componentes de referencia (a mano) -----------------------------------------------
class FRGPolicy:
    """Slot `construction_policy`: FRG (Araya y Toledo 2023) como política con memoria. La
    memoria es el estado de FRG congelado (pila en reducción sr, asignación A, destinos Sd,
    veces que se redujo cada pila); `score` da 0 al movimiento que haría FRG desde (parcial,
    memoria) y 1 al resto; `update` avanza el estado si la acción es la de FRG y, si no, abandona
    la reducción en curso (como un movimiento simple en BS-FRG). El greedy con esta política es
    FRG paso a paso; como rollout de la beam search, BS-FRG. Si el movimiento de FRG vuelve a un
    layout ya recorrido, la vista no lo ofrece y todos valen 1: decide el desempate."""

    COMPONENT = {"name": "frg_policy", "slot": "construction_policy", "params": {"prevent": {"type": "bool"}}}
    CACHE = 4096

    def __init__(self, problem=None, prevent: bool = True, r: int = 1):
        self.cfg = FRGConfig(r=r, prevent=prevent, assignment="never")
        self._step: dict = {}  # (layout, memoria) → (movimiento de FRG, memoria siguiente); acotado

    def _frg(self, L: Layout, memory: tuple):
        k = (L.state(), memory)
        if k not in self._step:
            if len(self._step) > self.CACHE:
                self._step.clear()
            st = FRGState.thaw(memory)
            q = L.copy(track=False)
            m = frg_step(q, st, self.cfg)
            self._step[k] = (m, st.freeze())
        return self._step[k]

    def init(self, L: Layout):
        return FRGState(reduced=[0] * L.S).freeze()

    def score(self, L: Layout, memory: tuple, a: Move) -> float:
        return 0.0 if self._frg(L, memory)[0] == (a.so, a.sd) else 1.0

    def update(self, L: Layout, memory: tuple, a: Move):
        m, nxt = self._frg(L, memory)
        if m == (a.so, a.sd):
            return nxt
        st = FRGState.thaw(memory)
        st.reset_reduction()
        return st.freeze()


class DestinationRank:
    """Slot `greedy_score`, miope: sacar un mal puesto antes que un bien puesto y, para el
    destino, el orden de `select_destination` (Araya y Toledo 2023, Alg. 1): XG con la menor
    diferencia de grupos, después XB a una desordenada de grupo menor, después el resto."""

    COMPONENT = {"name": "destination_rank", "slot": "greedy_score", "params": {}}

    def __init__(self, problem=None):
        self.problem = problem

    def score(self, L: Layout, a: Move) -> float:
        cat, val, _ = destination_rank(L, L.g(a.so), a.sd)
        return 1000.0 * (cat + 4 * L.is_sorted_stack(a.so)) + val


class FRGConstructor:
    """Slot `constructor`: FRG completo. Con `assignment="fallback"` reintenta con la
    asignación si sin ella no termina; si aun así no ordena, termina con el respaldo de la vista."""

    COMPONENT = {"name": "frg", "slot": "constructor",
                 "params": {"prevent": {"type": "bool"}, "assignment": {"type": "cat", "values": ["fallback", "always", "never"]}}}

    def __init__(self, problem=None, prevent: bool = True, assignment: str = "fallback", r: int = 1):
        self.problem = problem
        self.cfg = FRGConfig(r=r, prevent=prevent, assignment=assignment)

    def build(self, inst: "CPMPInstance", rng: Random):
        from .problem_model import CPMPModel, CPMPSolution

        q, ok = frg(Layout.from_instance(inst), self.cfg)
        if ok:
            return CPMPSolution(tuple(q.moves))
        P = self.problem if self.problem is not None else CPMPModel(inst)
        view = P.construction_view(inst)
        return view.complete(view.empty(), rng)


__all__ = ["Move", "CPMPConstructionView", "FRGPolicy", "DestinationRank", "FRGConstructor", "DEFAULT"]
