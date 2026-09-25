"""ILS (Iterated Local Search) como configuración del esqueleto genérico (§5.1).

Slots obligatorios: Constructor, LS interno (esqueleto embebido, p.ej.
Hill Climbing), Perturbación, Aceptación. ILS es de "segundo orden": el
slot de búsqueda local admite otro esqueleto instanciado como valor —
aquí simplemente una función `local_search(sol, rng) -> Solution`, que
puede ser el `hill_climb` provisto o cualquier otra cosa (incluida una
reparación MIP, que es la puerta de entrada natural a LNS-MIP: ver
`lns_mip.py`, que reutiliza esta misma idea con
`Perturbación = Destrucción` y `LS = Reparación MIP`).
"""

from __future__ import annotations

import time
from random import Random
from typing import Callable

from core.contracts import (
    Acceptance,
    Constructor,
    Neighborhood,
    Perturbation,
    ProblemModel,
    StopCriterion,
)
from core.neighborhood import sample_moves
from core.skeleton import SearchState, TrajectorySkeleton

LocalSearch = Callable[["object", Random], "object"]


def hill_climb(
    problem: ProblemModel,
    neighborhood: Neighborhood,
    strategy: str = "best",
    max_iters: int | None = None,
    max_seconds: float | None = None,
    sample_size: int | None = None,
) -> LocalSearch:
    """Búsqueda local simple sobre `neighborhood`, usable como slot "LS interno" de ILS.

    `strategy`: "first" (primera mejora) o "best" (mejor mejora). Se
    detiene al no encontrar mejora, al alcanzar `max_iters`, o al agotar
    `max_seconds` (revisado también *dentro* del barrido del vecindario:
    cuando cada `delta` cuesta un LP, un barrido completo puede tardar
    segundos y sin este chequeo la LS interna se come el presupuesto del
    esqueleto que la contiene).

    `sample_size`: si se da, cada paso evalúa solo una muestra al azar de hasta ese
    número de movimientos (`core.neighborhood.sample_moves`) y la búsqueda termina
    cuando una muestra no trae mejora. Con `None` recorre el vecindario completo en el
    orden de `moves`; cortado por tiempo, ese recorrido evalúa siempre los mismos
    primeros movimientos.
    """

    def _local_search(sol, rng: Random):
        deadline = None if max_seconds is None else time.monotonic() + max_seconds
        current = sol
        iters = 0
        while max_iters is None or iters < max_iters:
            best_move, best_delta = None, 0.0
            for m in sample_moves(neighborhood, current, sample_size, rng):
                if deadline is not None and time.monotonic() >= deadline:
                    break
                delta = neighborhood.delta(current, m)
                if delta < best_delta:
                    best_move, best_delta = m, delta
                    if strategy == "first":
                        break
            if best_move is None:
                break
            current = neighborhood.apply(current, best_move)
            iters += 1
            if deadline is not None and time.monotonic() >= deadline:
                break
        return current

    return _local_search


def build_ils(
    problem: ProblemModel,
    constructor: Constructor,
    local_search: LocalSearch,
    perturbation: Perturbation,
    acceptance: Acceptance,
    stop: StopCriterion,
    strength: float = 1.0,
    record_history: bool = False,
) -> TrajectorySkeleton:
    def candidate_generator(sol, state: SearchState, rng: Random):
        # ILS estándar: s* = LS(s0) antes de la primera perturbación. Sin esto la solución
        # inicial nunca pasa por la búsqueda local y, partiendo de un buen constructor, el
        # ILS puede no mejorarla nunca (validación por combinación, partida greedy).
        if not state.extra.get("_ils_started"):
            state.extra["_ils_started"] = True
            return local_search(sol, rng)
        perturbed = perturbation.perturb(sol, strength, rng)
        return local_search(perturbed, rng)

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=acceptance,
        stop=stop,
        state_updaters=[],
        record_history=record_history,
    )
