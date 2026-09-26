"""MIP-guided Perturbation (§5.2) como configuración del esqueleto genérico.

ILS cuya perturbación la resuelve el MIP:

    partial, free ← DESTROY(sol, ratio)                   # qué zona se re-optimiza
    F             ← `flips` variables de `free` en 1 en la incumbente (si no hay, cualquiera)
    fixed         ← to_assignment(sol) fuera de `free`, más las de F fijadas al valor contrario
    x             ← solve(modelo, fixed, integer = free − F)   # la mejor solución que cambia F
    candidato     ← LS(from_assignment(x))                 # búsqueda local con el vecindario
    aceptar si mejora

La perturbación de un ILS clásico es ciega (una patada al azar) y la reparación de LNS-MIP
no obliga a moverse (con la zona liberada, el sub-MIP puede devolver la misma solución).
Aquí la patada es mínima y forzada (apagar `flips` variables de la incumbente) y el MIP
elige la mejor forma de acomodar el resto de la zona; después la búsqueda local pule.
No requiere nada nuevo del `MIPModel`: forzar el cambio se expresa con `fixed`.

Slots: Constructor, Destrucción (elige la zona), Vecindario (búsqueda local), Parada.
"""

from __future__ import annotations

from random import Random

from core.common_components import BetterAcceptance
from core.contracts import Constructor, Destruction, ProblemModel, StopCriterion
from core.skeleton import RunResult, SearchState, TrajectorySkeleton
from skeletons.ils import LocalSearch


def build_mip_perturbation(
    problem: ProblemModel,
    constructor: Constructor,
    destruction: Destruction,
    local_search: LocalSearch,
    stop: StopCriterion,
    destroy_ratio: float = 0.2,
    flips: int = 1,
    mip_time_limit: float = 1.0,
    record_history: bool = False,
) -> TrajectorySkeleton:
    def candidate_generator(sol, state: SearchState, rng: Random):
        model = state.extra.get("mip_model")
        if model is None:
            model = problem.build_mip(state.extra["_inst"])
            state.extra["mip_model"] = model
        if not state.extra.get("_started"):  # como en ILS: búsqueda local sobre la inicial primero
            state.extra["_started"] = True
            return local_search(sol, rng)
        _partial, free = destruction.destroy(sol, destroy_ratio, rng)
        x_bar = problem.to_assignment(sol)
        free = sorted(free)
        ones = [v for v in free if x_bar.get(v, 0.0) > 0.5]
        pool = ones or free
        forced = set(rng.sample(pool, min(max(1, flips), len(pool)))) if pool else set()
        fixed = {v: val for v, val in x_bar.items() if v not in free}
        fixed.update({v: 1.0 - round(x_bar.get(v, 0.0)) for v in forced})
        x = model.solve(fixed=fixed, integer=set(free) - forced, relaxed=set(), time_limit=mip_time_limit,
                        warm_start=None)
        if x is None:
            return None
        return local_search(problem.from_assignment(x), rng)

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=BetterAcceptance(),
        stop=stop,
        record_history=record_history,
    )


def run_mip_perturbation(skeleton: TrajectorySkeleton, inst, rng: Random) -> RunResult:
    return skeleton.run(inst, rng, initial_extra={"_inst": inst})
