"""Vista constructiva del CVRP (`core.contracts.ConstructionView`).

Estado parcial: rutas abiertas (con su carga) y clientes pendientes. Acción: insertar un
cliente pendiente en una posición de una ruta donde cabe su demanda, o abrir una ruta
nueva con él. Con flota libre abrir una ruta siempre es factible, así que nunca hay
callejón sin salida: `complete` existe por contrato y abre una ruta por pendiente.

Contraste con el CLSP: allí decidir si un parcial se puede completar es NP-completo y
los candidatos se filtran con una condición necesaria; aquí la factibilidad es local
(cabe o no cabe en la ruta) y todos los candidatos son completables.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # `problem_model` re-exporta los tipos de aquí: importarlo al cargar sería circular
    from .problem_model import CVRPInstance


@dataclass(frozen=True)
class InsertAction:
    """Insertar `customer` en la ruta `route` en la posición `pos` (0 = primero). Si
    `new_route` es True, se abre una ruta nueva (`route` = len(rutas), `pos` = 0).
    `delta` es el aumento de distancia que produce la inserción."""

    customer: int
    route: int
    pos: int
    delta: float
    new_route: bool


class CVRPPartial:
    """Estado parcial (se copia en cada `apply`; nunca se modifica en su lugar).

    Atributos que puede leer un puntaje:
      inst                  la CVRPInstance (coords, demand, capacity, dist(i, j), n_customers)
      routes[k]             lista de clientes de la ruta k, en orden
      loads[k]              carga de la ruta k
      pending               frozenset de clientes sin asignar
    """

    __slots__ = ("inst", "routes", "loads", "pending")

    def __init__(self, inst: CVRPInstance, routes, loads, pending):
        self.inst, self.routes, self.loads, self.pending = inst, routes, loads, pending

    def copy(self) -> "CVRPPartial":
        return CVRPPartial(self.inst, [list(r) for r in self.routes], list(self.loads), self.pending)


class CVRPConstructionView:
    def __init__(self, problem, inst: CVRPInstance):
        self.problem, self.inst = problem, inst

    def empty(self) -> CVRPPartial:
        return CVRPPartial(self.inst, [], [], frozenset(self.inst.customers))

    def candidates(self, p: CVRPPartial):
        inst = self.inst
        out = []
        for c in sorted(p.pending):
            d = inst.demand[c]
            for k, route in enumerate(p.routes):
                if p.loads[k] + d > inst.capacity + 1e-9:
                    continue
                nodes = (0, *route, 0)
                for pos in range(len(nodes) - 1):
                    a, b = nodes[pos], nodes[pos + 1]
                    out.append(InsertAction(c, k, pos, inst.dist(a, c) + inst.dist(c, b) - inst.dist(a, b), False))
            out.append(InsertAction(c, len(p.routes), 0, 2 * inst.dist(0, c), True))
        return out

    def apply(self, p: CVRPPartial, a: InsertAction) -> CVRPPartial:
        n = p.copy()
        if a.new_route:
            n.routes.append([a.customer])
            n.loads.append(self.inst.demand[a.customer])
        else:
            n.routes[a.route].insert(a.pos, a.customer)
            n.loads[a.route] += self.inst.demand[a.customer]
        n.pending = p.pending - {a.customer}
        return n

    def is_complete(self, p: CVRPPartial) -> bool:
        return not p.pending

    def to_solution(self, p: CVRPPartial):
        from .problem_model import canonical

        return canonical(p.routes)

    def complete(self, p: CVRPPartial, rng: Random):
        from .problem_model import canonical

        return canonical([*p.routes, *([c] for c in sorted(p.pending))])


class CheapestInsertion:
    """Puntaje de referencia: el aumento de distancia de la inserción."""

    def __init__(self, problem):
        pass

    def score(self, p: CVRPPartial, a: InsertAction) -> float:
        return a.delta


class NearestFromDepot:
    """Puntaje de referencia: atender primero a los clientes cercanos al depósito, cada uno
    en la posición más barata."""

    def __init__(self, problem):
        self.inst = problem.inst

    def score(self, p: CVRPPartial, a: InsertAction) -> float:
        return 1000.0 * self.inst.dist(0, a.customer) + a.delta
