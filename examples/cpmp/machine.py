"""FRG (Araya y Toledo 2023) como máquina de estados del slot `construction_machine`
(`core.machine.MachinePolicy`):

    fill   --(no queda movimiento BG)-->                         reduce(sr)  [al entrar: select_reduce_stack]
    reduce --(sr vacía, u ordenada y con el criterio de parada)-->  fill si hay BG, si no reduce(otra sr)

- `fill`: puntúa los movimientos BG por g(sd) − g(so) (el Alg. 2) y el resto muy alto.
- `reduce`: puntúa los movimientos que sacan el tope de sr por el orden de `select_destination`.

Memoria: (pila en reducción o None, veces que se redujo cada pila). El greedy con esta máquina
hace los mismos movimientos que FRG sin la asignación de la §4.3.2 (`FRGConfig(assignment="never")`).
Es un componente de referencia escrito a mano, como `frg` y `frg_policy`: entra al catálogo y
sirve de semilla para la etapa `improve`, pero el LLM no lo ve cuando genera máquinas desde cero.
"""

from __future__ import annotations

from .frg import bg_moves, destination_rank, select_reduce_stack, stop_reduction
from .layout import Layout

FAR = 1e6  # puntaje de un movimiento que el estado no haría


class FRGMachine:
    COMPONENT = {"name": "frg_machine", "slot": "construction_machine",
                 "params": {"prevent": {"type": "bool", "default": True}, "r": {"type": "int", "range": [0, 3], "default": 1}}}
    states = ("fill", "reduce")

    def __init__(self, problem=None, prevent: bool = True, r: int = 1):
        self.prevent, self.r = prevent, r
        self._last: tuple | None = None  # (estado del layout, BG): se consulta por candidato

    def _bg(self, L: Layout) -> dict:
        k = L.state()
        if self._last is None or self._last[0] != k:
            self._last = (k, bg_moves(L, self.prevent))
        return self._last[1]

    def initial(self, L: Layout):
        return "fill", (None, (0,) * L.S)

    def _start_reduction(self, L: Layout, reduced: tuple):
        sr = select_reduce_stack(L, list(reduced))
        if sr is None:
            return "reduce", (None, reduced)
        return "reduce", (sr, reduced[:sr] + (reduced[sr] + 1,) + reduced[sr + 1:])

    def transition(self, L: Layout, state: str, memory):
        sr, reduced = memory
        if state == "reduce" and sr is not None and L.stacks[sr] and not stop_reduction(L, sr, self.r):
            return state, memory  # la reducción sigue
        if self._bg(L):
            return "fill", (None, reduced)
        return self._start_reduction(L, reduced)

    def score(self, L: Layout, state: str, memory, a) -> float:
        if state == "fill":
            d = self._bg(L).get((a.so, a.sd))
            return FAR if d is None else float(d)
        sr = memory[0]
        if a.so != sr:
            return FAR
        cat, val, sd = destination_rank(L, L.g(sr), a.sd)
        return 1000.0 * cat + 10.0 * val + sd / 100.0  # el orden lexicográfico de select_destination

    def update(self, L: Layout, state: str, memory, a):
        return memory


__all__ = ["FRGMachine"]
