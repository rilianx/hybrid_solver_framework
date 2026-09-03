"""VNS (Variable Neighborhood Search) como configuración del esqueleto genérico (§5.1).

Slots: Constructor, **lista ordenada de Vecindarios**, Parada. Estado
propio: índice k. Parámetros: `k_max` (implícito en la longitud de la
lista), `shake_strength`.

    candidato ← LS( SHAKE_k(sol) )        # shake: movimiento aleatorio en N_k, repetido shake_strength veces
    si f(candidato) < f(sol): sol ← candidato; k ← 1
    si no: k ← k + 1 (cíclico)

El "LS" es `hill_climb` sobre el primer vecindario de la lista (VND
básico se obtiene pasando como primer vecindario uno compuesto). Es un
esqueleto de segundo orden como ILS: la búsqueda local es un componente.
"""

from __future__ import annotations

from random import Random
from typing import Callable, Sequence

from core.common_components import BetterAcceptance
from core.contracts import Constructor, Neighborhood, ProblemModel, StopCriterion
from core.skeleton import SearchState, TrajectorySkeleton
from skeletons.ils import LocalSearch, hill_climb


def build_vns(
    problem: ProblemModel,
    constructor: Constructor,
    neighborhoods: Sequence[Neighborhood],
    stop: StopCriterion,
    local_search: LocalSearch | None = None,
    shake_strength: int = 1,
    ls_max_seconds: float | None = None,
    record_history: bool = False,
) -> TrajectorySkeleton:
    if not neighborhoods:
        raise ValueError("VNS necesita al menos un vecindario")
    ls = local_search or hill_climb(problem, neighborhoods[0], strategy="first", max_seconds=ls_max_seconds)

    def shake(sol, k: int, rng: Random):
        nbh = neighborhoods[k]
        cur = sol
        for _ in range(shake_strength):
            moves = list(nbh.moves(cur))
            if not moves:
                break
            cur = nbh.apply(cur, rng.choice(moves))
        return cur

    def candidate_generator(sol, state: SearchState, rng: Random):
        k = state.extra.get("k", 0)
        cand = ls(shake(sol, k, rng), rng)
        f_cur = state.current_objective if state.current_objective is not None else problem.objective(sol)
        improved = problem.objective(cand) < f_cur
        state.extra["k"] = 0 if improved else (k + 1) % len(neighborhoods)
        return cand

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=BetterAcceptance(),
        stop=stop,
        record_history=record_history,
    )
