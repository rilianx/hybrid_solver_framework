"""TS (Tabu Search) como configuración del esqueleto genérico (§5.1).

Slots: Constructor, Vecindario, Memoria (lista tabú), Parada. Estado
propio: la memoria vive dentro del componente `Memory` (tenencia,
frecuencias). Parámetros del esqueleto: `tenure`, `candidate_size`.

El generador de candidatos elige el *mejor* movimiento no tabú (o tabú
pero que cumple aspiración) entre una muestra de `candidate_size`
movimientos; la aceptación es "siempre" (TS se mueve al mejor vecino
aunque empeore), por eso el bucle genérico lo recibe con `AlwaysAccept`.
"""

from __future__ import annotations

from collections import deque
from random import Random

from core.common_components import AlwaysAccept
from core.contracts import Constructor, Memory, Neighborhood, ProblemModel, StopCriterion
from core.skeleton import SearchState, TrajectorySkeleton


class TabuMemory:
    """Memoria tabú genérica sobre movimientos hashables (slot `memory`).

    Prohíbe el movimiento *inverso* del aplicado si el vecindario expone
    `inverse(m)`; si no, prohíbe el mismo movimiento (correcto para
    movimientos auto-inversos como los flips). Aspiración: se permite un
    movimiento tabú si lleva a una solución mejor que la mejor conocida.
    """

    def __init__(self, tenure: int = 7, neighborhood: Neighborhood | None = None):
        self.tenure = tenure
        self.neighborhood = neighborhood
        self._queue: deque = deque()
        self._tabu: dict = {}
        self.best_seen = float("inf")

    def _key(self, m):
        inv = getattr(self.neighborhood, "inverse", None)
        return inv(m) if inv is not None else m

    def forbid(self, m, state: SearchState) -> None:
        key = self._key(m)
        self._queue.append(key)
        self._tabu[key] = self._tabu.get(key, 0) + 1
        while len(self._queue) > self.tenure:
            old = self._queue.popleft()
            self._tabu[old] -= 1
            if self._tabu[old] <= 0:
                del self._tabu[old]

    def is_tabu(self, m, state: SearchState) -> bool:
        return m in self._tabu

    def aspiration(self, m, f: float) -> bool:
        return f < self.best_seen


def build_ts(
    problem: ProblemModel,
    constructor: Constructor,
    neighborhood: Neighborhood,
    stop: StopCriterion,
    memory: Memory | None = None,
    tenure: int = 7,
    candidate_size: int = 30,
    record_history: bool = False,
) -> TrajectorySkeleton:
    memory = memory or TabuMemory(tenure=tenure, neighborhood=neighborhood)

    def candidate_generator(sol, state: SearchState, rng: Random):
        moves = list(neighborhood.moves(sol))
        if not moves:
            return None
        if len(moves) > candidate_size:
            moves = rng.sample(moves, candidate_size)
        f_sol = state.current_objective if state.current_objective is not None else problem.objective(sol)
        if hasattr(memory, "best_seen"):
            memory.best_seen = min(memory.best_seen, state.best_objective if state.best_objective is not None else f_sol)
        best_m, best_d = None, float("inf")
        for m in moves:
            d = neighborhood.delta(sol, m)
            if memory.is_tabu(m, state) and not memory.aspiration(m, f_sol + d):
                continue
            if d < best_d:
                best_m, best_d = m, d
        if best_m is None:
            return None
        memory.forbid(best_m, state)
        return neighborhood.apply(sol, best_m)

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=AlwaysAccept(),
        stop=stop,
        record_history=record_history,
    )
