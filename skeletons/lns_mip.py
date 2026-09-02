"""LNS-MIP como configuración del esqueleto genérico (§5.2/§5.3).

Es literalmente ILS con `Perturbación = Destrucción` y
`LS = Reparación MIP`: el mismo `TrajectorySkeleton`, con un
`candidate_generator` que destruye una fracción de la solución y
resuelve el sub-MIP sobre las variables liberadas, dejando el resto
fijo (warm-started con la solución actual).

    partial, free ← DESTROY(sol, ratio)
    fixed         ← to_assignment(sol) restringido a variables no libres
    candidato     ← REPAIR_MIP(model, fixed, free, time_limit, warm_start=to_assignment(sol))
"""

from __future__ import annotations

from random import Random
from typing import Callable, Optional

from core.contracts import (
    Acceptance,
    Constructor,
    Destruction,
    ProblemModel,
    RepairMIP,
    StopCriterion,
)
from core.skeleton import RunResult, SearchState, TrajectorySkeleton

# adapt_ratio(ratio_actual, candidato, sol_actual, problem) -> nuevo_ratio
AdaptRatio = Callable[[float, object | None, object, ProblemModel], float]


def default_adapt_ratio(ratio: float, cand, sol, problem: ProblemModel) -> float:
    """Sin adaptación: mantiene el ratio de destrucción fijo."""
    return ratio


def build_lns_mip(
    problem: ProblemModel,
    constructor: Constructor,
    destruction: Destruction,
    repair_mip: RepairMIP,
    acceptance: Acceptance,
    stop: StopCriterion,
    destroy_ratio: float = 0.2,
    mip_time_limit: float = 5.0,
    adapt_ratio: Optional[AdaptRatio] = None,
    record_history: bool = False,
) -> TrajectorySkeleton:
    adapt_ratio = adapt_ratio or default_adapt_ratio

    def candidate_generator(sol, state: SearchState, rng: Random):
        model = state.extra.get("mip_model")
        if model is None:
            model = problem.build_mip(state.extra["_inst"])
            state.extra["mip_model"] = model

        ratio = state.extra["ratio"]
        _partial, free = destruction.destroy(sol, ratio, rng)
        full_assignment = problem.to_assignment(sol)
        fixed = {v: val for v, val in full_assignment.items() if v not in free}

        cand = repair_mip.repair_mip(
            model,
            fixed,
            free,
            time_limit=mip_time_limit,
            warm_start=full_assignment,
        )

        state.extra["ratio"] = adapt_ratio(ratio, cand, sol, problem)
        return cand

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=acceptance,
        stop=stop,
        state_updaters=[],
        record_history=record_history,
    )


def run_lns_mip(
    skeleton: TrajectorySkeleton, inst, rng: Random, destroy_ratio: float
) -> RunResult:
    """Envuelve `skeleton.run` para inyectar `_inst` y el `ratio` inicial en el estado.

    Necesario porque `build_mip(inst)` solo puede construirse una vez
    conocida la instancia, y el contrato de `candidate_generator` (§ core.skeleton)
    no recibe `inst` explícitamente.
    """
    return skeleton.run(inst, rng, initial_extra={"_inst": inst, "ratio": destroy_ratio})
