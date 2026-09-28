"""Vista constructiva del CPMP (`core.contracts.ConstructionView`).

Estado parcial: el `Layout` con los movimientos hechos y el estado de FRG. Acciones, como
en BS*-FRG (Araya y Toledo 2023, §5):

- `Move(so, sd)`: movimiento simple. Por cada pila de origen solo los `k` mejores destinos
  según `select_destination` (k = None: todos). No se ofrece deshacer el último movimiento.
  Cancela la reducción en curso (sr ← ∅).
- `FRGStep()`: una iteración de FRG, que conserva su estado (sr, A, Sd): no es lo mismo
  que el movimiento simple equivalente.
- `Reduce(s)` (con `compound=True`): movimiento compuesto R_s, reducir s hasta el criterio.

Un parcial está completo cuando el layout está ordenado. `complete` corre FRG desde el
parcial (y, si desde ahí no termina, desde el layout inicial): es el respaldo del bucle
greedy y el rollout de la beam search (`rollout="complete"`), así que BS-FRG es
`BeamSearchConstructor(P, rollout="complete")` sobre esta vista.
`lower_bound` = movimientos hechos + mal puestos; `key` identifica layouts repetidos.
A partir de `max_moves` movimientos no hay candidatos: el greedy termina con FRG.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from .frg import DEFAULT, FRGConfig, Layout, default_max_moves, destination_rank, frg, frg_step, ranked_destinations, reduce_stack

if TYPE_CHECKING:
    from .instance import CPMPInstance


@dataclass(frozen=True)
class Move:
    so: int
    sd: int


@dataclass(frozen=True)
class FRGStep:
    pass


@dataclass(frozen=True)
class Reduce:
    stack: int


class CPMPConstructionView:
    def __init__(self, problem, inst: "CPMPInstance", k: int | None = 3, compound: bool = True,
                 frg_action: bool = True, frg_config: FRGConfig = DEFAULT, max_moves: int | None = None):
        self.problem, self.inst = problem, inst
        self.k, self.compound, self.frg_action = k, compound, frg_action
        self.cfg = frg_config
        self.max_moves = max_moves

    def _limit(self, L: Layout) -> int:
        return default_max_moves(L) if self.max_moves is None else self.max_moves

    def empty(self) -> Layout:
        return Layout.from_instance(self.inst)

    def candidates(self, L: Layout):
        if L.is_sorted() or L.dead or len(L.moves) >= self._limit(L):
            return []
        out: list = [FRGStep()] if self.frg_action else []
        last = L.moves[-1] if L.moves else None
        for so in range(L.S):
            if not L.stacks[so]:
                continue
            dests = [sd for sd in ranked_destinations(L, so) if (sd, so) != last]
            out += [Move(so, sd) for sd in (dests if self.k is None else dests[: self.k])]
        if self.compound:
            out += [Reduce(s) for s in range(L.S) if L.stacks[s]]
        return out

    def apply(self, L: Layout, a) -> Layout:
        q = L.copy()
        if isinstance(a, Move):
            q.reset_reduction()
            q.move(a.so, a.sd)
        elif isinstance(a, FRGStep):
            frg_step(q, self.cfg)
        elif isinstance(a, Reduce):
            if not reduce_stack(q, a.stack, self.cfg, self._limit(q)):
                q.dead = True
        else:
            raise TypeError(f"acción desconocida {a!r}")
        return q

    def is_complete(self, L: Layout) -> bool:
        return L.is_sorted()

    def to_solution(self, L: Layout):
        from .problem_model import CPMPSolution

        return CPMPSolution(tuple(L.moves))

    def complete(self, L: Layout, rng: Random):
        q = frg(L, self.cfg)
        if q.dead:  # desde este parcial FRG no termina (p.ej. un greedy que ciclaba): FRG desde el inicio
            q = frg(self.empty(), self.cfg)
        return self.to_solution(q)

    def lower_bound(self, L: Layout) -> int:
        return len(L.moves) + L.bad()

    def key(self, L: Layout):
        return L.key()


class FRGConstructor:
    """FRG completo como constructor (slot `constructor`): con `assignment="fallback"`
    reintenta desde el layout inicial con la asignación si sin ella no termina."""

    COMPONENT = {"name": "frg", "slot": "constructor",
                 "params": {"prevent": {"type": "bool"}, "assignment": {"type": "cat", "values": ["fallback", "always", "never"]}}}

    def __init__(self, problem=None, prevent: bool = True, assignment: str = "fallback", r: int = 1):
        self.cfg = FRGConfig(r=r, prevent=prevent, assignment=assignment)

    def build(self, inst: "CPMPInstance", rng: Random):
        from .problem_model import CPMPSolution

        return CPMPSolution(tuple(frg(Layout.from_instance(inst), self.cfg).moves))


# --- puntajes de mano (slot greedy_score; MENOR es mejor) -----------------------------
class FRGPolicy:
    """Siempre la iteración de FRG: el greedy con este puntaje ES FRG."""

    COMPONENT = {"name": "frg_policy", "slot": "greedy_score", "params": {}}

    def __init__(self, problem):
        self.problem = problem

    def score(self, L: Layout, a) -> float:
        return 0.0 if isinstance(a, FRGStep) else 1.0


class FillFirst:
    """Llenar antes que seguir reduciendo: el BG de menor g(sd) − g(so) apenas exista uno
    (aunque corte la reducción en curso) y, si no hay, la iteración de FRG. Es la variante
    más obvia de FRG como puntaje sobre acciones; sirve de segundo punto de comparación."""

    COMPONENT = {"name": "fill_first", "slot": "greedy_score", "params": {}}

    def __init__(self, problem):
        self.problem = problem

    def score(self, L: Layout, a) -> float:
        if isinstance(a, FRGStep):
            return 1e3
        if isinstance(a, Move) and not L.is_sorted_stack(a.so) and L.is_sorted_stack(a.sd) and L.g(a.sd) >= L.g(a.so):
            return float(L.g(a.sd) - L.g(a.so))
        return 1e6


__all__ = ["FRGConstructor", "Move", "FRGStep", "Reduce", "CPMPConstructionView", "FRGPolicy", "FillFirst"]
