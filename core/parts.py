"""Orígenes y colocación: una acción se separa en QUÉ se mueve y ADÓNDE.

En FRG un movimiento son dos decisiones: qué pila es el origen y a qué pila va su tope. El destino
lo decide siempre la misma colocación (`destination_rank`); lo que cambia entre `bg` y la reducción
es solo cómo se elige el origen. Así una heurística como FRG son tres piezas simples:

    class Colocacion:                                  # común a todos los orígenes
        name = "tight_fit"
        rank(parcial, acción) -> clave                 # menor = mejor (un número o una tupla)

    class Origen:                                      # p.ej. bg, reducción
        name = "bg"
        sources(parcial, memoria) -> [orígenes]        # en orden de preferencia; [] = no aplica
        init(parcial) -> memoria                       # opcional (default ())
        update(parcial, memoria, acción) -> memoria    # opcional: tras hacer una de sus acciones

El pack dice qué es el origen de una acción con `view.source(acción)` (en el CPMP, la pila `so`).
Un origen se vuelve una regla de `core.rules` (`SourceRule`): permite los candidatos que salen de
sus orígenes, en ese orden, y entre los de un mismo origen los ordena la colocación. Sin
colocación, la de la vista: la acción que menos sube la cota inferior. Como son reglas comunes,
el greedy, la beam search, la validación y el diagnóstico las usan sin cambios.

    origin_machine(problem, Origen())          # una máquina de una regla (pieza de origen)
    placement_machine(problem, Colocacion())   # una máquina de una regla que permite todo, ordenado
                                               # por la colocación (pieza de colocación)
"""

from __future__ import annotations

from typing import Any

from .rules import RuleMachine


def supports_parts(view: Any) -> bool:
    return callable(getattr(view, "source", None))


class SourceRule:
    """Un origen como regla: los candidatos de sus orígenes, cada grupo ordenado por la colocación."""

    def __init__(self, origin: Any, placement: Any = None):
        self.origin, self.placement = origin, placement
        self.name = getattr(origin, "name", None)
        self.priority = getattr(origin, "priority", 100)
        self.machine: RuleMachine | None = None  # la máquina que la contiene (para la vista)

    def init(self, partial):
        fn = getattr(self.origin, "init", None)
        return fn(partial) if callable(fn) else ()

    def update(self, partial, memory, action):
        fn = getattr(self.origin, "update", None)
        return fn(partial, memory, action) if callable(fn) else memory

    def _key(self, view, partial):
        if self.placement is not None:
            return lambda a: self.placement.rank(partial, a)
        lb = getattr(view, "lower_bound", None)
        if callable(lb):
            return lambda a: lb(view.apply(partial, a))
        return lambda a: 0

    def allowed(self, partial, memory, candidates):
        srcs = list(self.origin.sources(partial, memory) or [])
        if not srcs:
            return []
        view = self.machine.view()
        by: dict = {}
        for a in candidates:
            by.setdefault(view.source(a), []).append(a)
        key = self._key(view, partial)
        out, seen = [], set()
        for s in srcs:
            if s in seen or s not in by:
                continue
            seen.add(s)
            out += sorted(by[s], key=key)
        return out


class PlacementRule(SourceRule):
    """Una colocación sola como regla: todos los candidatos, ordenados por ella (una pieza ancha)."""

    def __init__(self, placement: Any):
        super().__init__(None, placement)
        self.name = getattr(placement, "name", None)

    def init(self, partial):
        return ()

    def update(self, partial, memory, action):
        return memory

    def allowed(self, partial, memory, candidates):
        return sorted(candidates, key=self._key(self.machine.view(), partial))


def _attach(machine: RuleMachine) -> RuleMachine:
    for r in machine.rules:
        if isinstance(r, SourceRule):
            r.machine = machine
    return machine


def origin_machine(problem: Any, origin: Any, placement: Any = None) -> RuleMachine:
    if not callable(getattr(origin, "sources", None)):
        raise ValueError(f"el origen `{getattr(origin, 'name', origin)}` necesita `sources(parcial, memoria)`")
    return _attach(RuleMachine(problem, [SourceRule(origin, placement)]))


def placement_machine(problem: Any, placement: Any) -> RuleMachine:
    if not callable(getattr(placement, "rank", None)):
        raise ValueError(f"la colocación `{getattr(placement, 'name', placement)}` necesita `rank(parcial, acción)`")
    return _attach(RuleMachine(problem, [PlacementRule(placement)]))


def compose_parts(problem: Any, origins: list, placement: Any = None, priorities=None) -> RuleMachine:
    """Una máquina con varios orígenes (en orden de prioridad) y una colocación común."""
    rules = []
    for k, o in enumerate(origins):
        r = SourceRule(o, placement)
        if priorities is not None:
            r.priority = priorities[k]
        rules.append(r)
    return _attach(RuleMachine(problem, rules))


def assemble(problem: Any, machines: list, priorities=None) -> RuleMachine:
    """Junta piezas (máquinas de una regla) en una máquina: los orígenes y las reglas comunes en ese
    orden de prioridad, y la colocación (si hay una pieza de colocación) para todos los orígenes. Una
    colocación sola es su propia máquina (permite todo, ordenado por ella)."""
    place, rules = None, []
    for m in machines:
        r = m.rules[0]
        if isinstance(r, PlacementRule):
            place = r.placement
        else:
            rules.append(r)
    if not rules and place is not None:
        return placement_machine(problem, place)
    for k, r in enumerate(rules):
        if priorities is not None:
            r.priority = priorities[k]
        if isinstance(r, SourceRule) and place is not None:
            r.placement = place
    return _attach(RuleMachine(problem, rules))


def kind_of(machine: Any) -> str:
    """"origin", "place" o "rule" (una regla común) según la primera regla de la máquina."""
    r = machine.rules[0] if getattr(machine, "rules", None) else None
    if isinstance(r, PlacementRule):
        return "place"
    if isinstance(r, SourceRule):
        return "origin"
    return "rule"


__all__ = ["SourceRule", "PlacementRule", "origin_machine", "placement_machine", "compose_parts", "assemble", "kind_of",
           "supports_parts"]
