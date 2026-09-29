from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from core.machine import FALLBACK
from core.rules import RuleMachine


@dataclass(frozen=True)
class Move:
    so: int
    sd: int


COMPONENT = {
    "name": "supporting_safe_move",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}


class SupportingSafeMoveRule:
    name = "supporting_safe_move"

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        return memory

    def update(self, partial, memory, action):
        return memory

    def done(self, partial, memory):
        return True

    def propose(self, partial, memory):
        """
        Prioriza movimientos que colocan el contenedor del tope sobre una pila que lo
        acepta sin romper la ordenación, favoreciendo destinos ya ordenados y/o vacíos.
        """
        candidates: List[Tuple[int, int, int, int, int]] = []
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue

                # Solo movimientos "seguros": el contenedor queda bien puesto en la pila destino.
                if partial.stacks[sd]:
                    if c > partial.g(sd):
                        continue

                # Preferencia:
                # 1) destino ya ordenado / vacío
                # 2) menor grupo en la cima de destino que aún acepte el contenedor
                # 3) source con más contenedores mal puestos desbloqueados
                dest_is_safe = 1 if (not partial.stacks[sd] or partial.is_sorted_stack(sd)) else 0
                dest_top = partial.g(sd) if partial.stacks[sd] else 0
                source_ub = partial.ub(so)

                candidates.append((-dest_is_safe, dest_top, -source_ub, so, sd))

        candidates.sort()
        return [Move(so, sd) for _, _, _, so, sd in candidates]


class SafePlacementTransitions:
    def initial(self, partial):
        return ()

    def select(self, partial, memory, rules):
        if rules.applies(SupportingSafeMoveRule.name):
            return SupportingSafeMoveRule.name, memory
        return FALLBACK, memory


def build_component(problem, **params):
    rule = SupportingSafeMoveRule()
    transitions = SafePlacementTransitions()
    return RuleMachine(problem, [rule], transitions)
