"""GRASP (Feo y Resende, 1995) como configuración del esqueleto genérico: varios arranques.

Cada iteración construye una solución nueva con el constructor y la mejora; el esqueleto se queda con la mejor. La
mejora (`improve`) es la búsqueda local hasta el óptimo local ("descent", el GRASP clásico), o un número fijo de
iteraciones de tabú ("ts") o de ILS con recocido ("ils"), como la mejora de PR (GRASP + TS, GRASP + ILS). La parte "greedy aleatorizada" es el constructor: uno que usa el `rng` (p.ej. con una
lista restringida de candidatos, como los que escribe el LLM) da una solución distinta en cada iteración. Con un
constructor determinista, las iteraciones solo difieren por la muestra de movimientos de la búsqueda local.
"""

from __future__ import annotations

from random import Random

import math

from core.common_components import AnyStop, MaxIterationsStop, MaxTimeStop
from core.contracts import Constructor, ProblemModel, StopCriterion
from core.skeleton import SearchState, TrajectorySkeleton
from skeletons.ils import LocalSearch


class AlwaysAccept:
    """Cada iteración reemplaza a la anterior; la mejor la guarda el esqueleto."""

    def accept(self, f_cur: float, f_cand: float, state: SearchState) -> bool:
        return True


def make_improve(problem, neighborhood, inst, improve: str = "descent", descent=None, iters: int = 500,
                 perturbation=None, strength: int = 1, T_rel: float = 0.005, tenure: int = 10, candidate_size: int = 30,
                 estimate_top: int = 0, left=lambda: float("inf")):
    """La mejora de cada arranque: `descent(sol, rng)` (una `hill_climb`), o `iters` iteraciones de tabú o de ILS con
    recocido (T = T_rel · f, que baja al 1 % en las iteraciones de cada mejora), cortadas por el tiempo que queda."""
    if improve == "descent":
        return descent
    if improve == "ils":
        if perturbation is None:
            raise ValueError("GRASP con improve = ils necesita una perturbación")

        def ils(sol, rng: Random):
            cur = descent(sol, rng)
            f = problem.objective(cur)
            best, fb = cur, f
            for i in range(iters):
                if left() <= 0:
                    break
                cand = descent(perturbation.perturb(cur, strength, rng), rng)
                fc, T = problem.objective(cand), T_rel * 0.01 ** (i / iters) * abs(f)
                if fc <= f or (T > 0 and rng.random() < math.exp(-(fc - f) / T)):
                    cur, f = cand, fc
                if f < fb:
                    best, fb = cur, f
            return best

        return ils
    from skeletons.pr import _Given
    from skeletons.ts import build_ts

    def ts(sol, rng: Random):
        stop = AnyStop((MaxIterationsStop(iters), MaxTimeStop(max(0.0, left()))))
        return build_ts(problem, _Given(sol), neighborhood, stop, tenure=tenure, candidate_size=candidate_size,
                        estimate_top=estimate_top).run(inst, rng).best_solution

    return ts


def run_grasp(problem, constructor, local_search, stop, inst, rng: Random):
    """Corre GRASP en `inst` con la mejora `local_search(sol, rng)` (el constructor necesita la instancia en cada
    iteración)."""
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
