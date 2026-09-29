"""FRG (Araya y Toledo 2023) como máquina de reglas (`core.rules.RuleMachine`): dos reglas de
acción y unas transiciones de tres líneas.

- `bg_move`: los movimientos BG (dejan bien puesto un mal puesto) ordenados por g(sd) − g(so)
  (el Alg. 2); no aplica si no hay.
- `reduce_stack`: al activarse elige la pila sr (`select_reduce_stack`: la menos veces reducida,
  ...); propone sacar el tope de sr a los destinos en el orden de `select_destination`; termina
  cuando sr queda vacía o cumple el criterio de parada (§4.1).
- Transiciones: `reduce_stack` mientras no termine; si no, `bg_move` si aplica; si no,
  `reduce_stack` (que al volver a activarse elige otra pila).

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
    name = "bg_move"

    def __init__(self, prevent: bool = True):
        self.prevent = prevent

    def propose(self, L: Layout, memory):
        moves = bg_moves(L, self.prevent)
        from .construction import Move

        return [Move(so, sd) for so, sd in sorted(moves, key=moves.__getitem__)]


class ReduceStack:
    """Memoria: (pila en reducción o None, veces que se redujo cada pila)."""

    name = "reduce_stack"

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

    def propose(self, L: Layout, memory):
        from .construction import Move

        sr = memory[0]
        if sr is None or not L.stacks[sr]:
            return []
        return [Move(sr, sd) for sd in ranked_destinations(L, sr)]

    def done(self, L: Layout, memory) -> bool:
        sr = memory[0]
        return sr is None or not L.stacks[sr] or stop_reduction(L, sr, self.r)


class FRGTransitions:
    def select(self, L: Layout, memory, rules):
        if rules.active == "reduce_stack" and not rules.done("reduce_stack"):
            return "reduce_stack", memory
        if rules.applies("bg_move"):
            return "bg_move", memory
        return "reduce_stack", memory


class FRGMachine(RuleMachine):
    COMPONENT = {"name": "frg_machine", "slot": "construction_machine",
                 "params": {"prevent": {"type": "bool", "default": True}, "r": {"type": "int", "range": [0, 3], "default": 1}}}

    def __init__(self, problem=None, prevent: bool = True, r: int = 1):
        super().__init__(problem, [BGMove(prevent), ReduceStack(r)], FRGTransitions())


__all__ = ["BGMove", "ReduceStack", "FRGTransitions", "FRGMachine"]
