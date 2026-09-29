"""FRG (Araya y Toledo 2023) como máquina de reglas (`core.rules.RuleMachine`): una regla simple
y una macro, con prioridades.

- `bg_move`: los movimientos BG (dejan bien puesto un mal puesto) ordenados por g(sd) − g(so)
  (el Alg. 2); no aplica si no hay.
- `reduce_stack`: al activarse elige la pila sr (`select_reduce_stack`: la menos veces reducida,
  ...); propone sacar el tope de sr a los destinos en el orden de `select_destination`; termina
  cuando sr queda vacía o cumple el criterio de parada (§4.1).
- Prioridades: `bg_move` 100, `reduce_stack` 50. El controlador de `core.rules` sigue la macro
  activa hasta que termine; si no, `bg_move` si aplica; si no, `reduce_stack` (que al volver a
  activarse elige otra pila).

El greedy con esta máquina hace los mismos movimientos que FRG sin la asignación de la §4.3.2
(`FRGConfig(assignment="never")`). Es un componente de referencia escrito a mano, como `frg` y
`frg_policy`: entra al catálogo y sirve de semilla para la etapa `evolve`, pero el LLM no lo ve
cuando genera máquinas desde cero.
"""

from __future__ import annotations

from core.rules import RuleMachine

from .frg import bg_moves, ranked_destinations, select_reduce_stack, stop_reduction
from .layout import Layout


class BGMove:
    """Regla simple: los movimientos BG, por g(sd) − g(so) (Alg. 2)."""

    name = "bg_move"
    priority = 100

    def __init__(self, prevent: bool = True):
        self.prevent = prevent

    def allowed(self, L: Layout, memory, candidates):
        moves = bg_moves(L, self.prevent)
        return sorted((c for c in candidates if (c.so, c.sd) in moves), key=lambda c: moves[(c.so, c.sd)])


class ReduceStack:
    """Macro: al activarse elige la pila sr; permite sacar su tope a los destinos en el orden de
    `select_destination`; termina cuando sr queda vacía o cumple el criterio de parada. Memoria:
    (sr o None, veces que se redujo cada pila)."""

    name = "reduce_stack"
    priority = 50

    def __init__(self, r: int = 1):
        self.r = r

    def init(self, L: Layout):
        return (None, (0,) * L.S)

    def start(self, L: Layout, memory):
        _, reduced = memory
        sr = select_reduce_stack(L, list(reduced))
        if sr is None:
            return (None, reduced)
        return (sr, reduced[:sr] + (reduced[sr] + 1,) + reduced[sr + 1:])

    def allowed(self, L: Layout, memory, candidates):
        sr = memory[0]
        if sr is None or not L.stacks[sr]:
            return []
        by_sd = {c.sd: c for c in candidates if c.so == sr}
        return [by_sd[sd] for sd in ranked_destinations(L, sr) if sd in by_sd]

    def done(self, L: Layout, memory) -> bool:
        sr = memory[0]
        return sr is None or not L.stacks[sr] or stop_reduction(L, sr, self.r)


class FRGMachine(RuleMachine):
    COMPONENT = {"name": "frg_machine", "slot": "construction_machine",
                 "params": {"prevent": {"type": "bool", "default": True}, "r": {"type": "int", "range": [0, 3], "default": 1}}}

    def __init__(self, problem=None, prevent: bool = True, r: int = 1):
        super().__init__(problem, [BGMove(prevent), ReduceStack(r)])


__all__ = ["BGMove", "ReduceStack", "FRGMachine"]
