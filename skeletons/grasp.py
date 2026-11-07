"""GRASP (Feo y Resende, 1995) como configuración del esqueleto genérico: varios arranques.

Cada iteración construye una solución nueva con el constructor y la lleva a un óptimo local con `hill_climb`; el
esqueleto se queda con la mejor. La parte "greedy aleatorizada" es el constructor: uno que usa el `rng` (p.ej. con una
lista restringida de candidatos, como los que escribe el LLM) da una solución distinta en cada iteración. Con un
constructor determinista, las iteraciones solo difieren por la muestra de movimientos de la búsqueda local.
"""

from __future__ import annotations

from random import Random

from core.contracts import Constructor, ProblemModel, StopCriterion
from core.skeleton import SearchState, TrajectorySkeleton
from skeletons.ils import LocalSearch


class AlwaysAccept:
    """Cada iteración reemplaza a la anterior; la mejor la guarda el esqueleto."""

    def accept(self, f_cur: float, f_cand: float, state: SearchState) -> bool:
        return True


def run_grasp(problem, constructor, local_search, stop, inst, rng: Random):
    """Corre GRASP en `inst` (el constructor necesita la instancia en cada iteración)."""
    return build_grasp(problem, constructor, local_search, stop).run(inst, rng, initial_extra={"_grasp_inst": inst})


def build_grasp(
    problem: ProblemModel,
    constructor: Constructor,
    local_search: LocalSearch,
    stop: StopCriterion,
    record_history: bool = False,
) -> TrajectorySkeleton:
    def candidate_generator(sol, state: SearchState, rng: Random):
        # la primera iteración mejora la solución con la que arrancó el esqueleto (ya construida)
        if not state.extra.get("_grasp_started"):
            state.extra["_grasp_started"] = True
            return local_search(sol, rng)
        return local_search(constructor.build(state.extra["_grasp_inst"], rng), rng)

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=AlwaysAccept(),
        stop=stop,
        state_updaters=[],
        record_history=record_history,
    )
