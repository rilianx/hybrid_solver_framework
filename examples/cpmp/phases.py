"""FRG (Araya y Toledo 2023) como dos fases del slot `phase` (`core.phases.PhasedPolicy`).

    PhasedPolicy([BGFill(), ReduceStack()])  ≈  FRG sin asignación (`FRGConfig(assignment="never")`)

- `BGFill` ("llenar"): aplica si hay un movimiento BG (deja bien puesto un mal puesto); puntúa
  los BG por g(sd) − g(so) y el resto muy alto. No retiene el control: en cada paso se vuelve a
  preguntar si hay BG, como en el Alg. 3.
- `ReduceStack` ("reducir"): el comodín (aplica siempre). Al tomar el control elige la pila sr
  (`select_reduce_stack`: la menos veces reducida, ...); puntúa los movimientos que sacan el
  tope de sr por el orden de `select_destination`; suelta el control cuando sr queda vacía o
  cumple el criterio de parada (§4.1).

Son componentes de referencia escritos a mano, como `frg` y `frg_policy`: entran al catálogo y
sirven de semilla para la etapa `improve`, pero el LLM no los ve cuando genera fases desde cero.
Lo que no está aquí: la asignación de la §4.3.2 (`unblocking_assignment`).
"""

from __future__ import annotations

from .frg import bg_moves, destination_rank, select_reduce_stack, stop_reduction
from .layout import Layout

FAR = 1e6  # puntaje de un movimiento que la fase no haría


class BGFill:
    COMPONENT = {"name": "bg_fill", "slot": "phase", "params": {"prevent": {"type": "bool", "default": True}}}

    def __init__(self, problem=None, prevent: bool = True):
        self.prevent = prevent
        self._last: tuple | None = None  # (estado del layout, BG): se consulta por candidato

    def _bg(self, L: Layout) -> dict:
        k = L.state()
        if self._last is None or self._last[0] != k:
            self._last = (k, bg_moves(L, self.prevent))
        return self._last[1]

    def init(self, L: Layout):
        return ()

    def applies(self, L: Layout, memory) -> bool:
        return bool(self._bg(L))

    def score(self, L: Layout, memory, a) -> float:
        d = self._bg(L).get((a.so, a.sd))
        return FAR if d is None else float(d)

    def update(self, L: Layout, memory, a):
        return memory


class ReduceStack:
    """Memoria: (pila en reducción o None, veces que se redujo cada pila)."""

    COMPONENT = {"name": "reduce_stack", "slot": "phase", "params": {"r": {"type": "int", "range": [0, 3], "default": 1}}}

    def __init__(self, problem=None, r: int = 1):
        self.r = r

    def init(self, L: Layout):
        return (None, (0,) * L.S)

    def start(self, L: Layout, memory):
        _, reduced = memory
        sr = select_reduce_stack(L, list(reduced))
        if sr is None:
            return memory
        return (sr, reduced[:sr] + (reduced[sr] + 1,) + reduced[sr + 1:])

    def score(self, L: Layout, memory, a) -> float:
        sr = memory[0]
        if a.so != sr:
            return FAR
        cat, val, sd = destination_rank(L, L.g(sr), a.sd)
        return 1000.0 * cat + 10.0 * val + sd / 100.0  # el orden lexicográfico de select_destination

    def update(self, L: Layout, memory, a):
        return memory

    def done(self, L: Layout, memory) -> bool:
        sr = memory[0]
        return sr is None or not L.stacks[sr] or stop_reduction(L, sr, self.r)


__all__ = ["BGFill", "ReduceStack"]
