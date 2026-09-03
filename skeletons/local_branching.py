"""Local Branching (§5.2/§5.3) como configuración del esqueleto genérico.

    modelo ← P.build_mip(inst); sol ← CONSTRUCTOR(inst); k ← k0
    mientras no PARADA():
        cand ← solve(modelo, near=(to_assignment(sol), k), time_limit)   # Σ|x − x̄| ≤ k
        si cand mejora: sol ← cand; k ← k0
        si no:          k ← k + k_step                                     # ampliar vecindario

El vecindario es la bola de Hamming de radio k alrededor de la incumbente,
explorada por el solver MIP. A diferencia de LNS-MIP no se fija nada: se
restringe la distancia. Requiere que el `MIPModel` soporte `near=`.
"""

from __future__ import annotations

from random import Random

from core.common_components import BetterAcceptance
from core.contracts import Constructor, ProblemModel, StopCriterion
from core.skeleton import RunResult, SearchState, TrajectorySkeleton


def build_local_branching(
    problem: ProblemModel,
    constructor: Constructor,
    stop: StopCriterion,
    k: int = 5,
    k_step: int = 3,
    k_max: int | None = None,
    time_limit: float = 5.0,
    record_history: bool = False,
) -> TrajectorySkeleton:
    def candidate_generator(sol, state: SearchState, rng: Random):
        model = state.extra.get("mip_model")
        if model is None:
            model = problem.build_mip(state.extra["_inst"])
            state.extra["mip_model"] = model
            state.extra["k"] = k
        x_bar = problem.to_assignment(sol)
        radius = state.extra["k"]
        x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=time_limit,
                        warm_start=x_bar, near=(x_bar, radius))
        cand = None if x is None else problem.from_assignment(x)
        f_cur = state.current_objective if state.current_objective is not None else problem.objective(sol)
        if cand is not None and problem.objective(cand) < f_cur:
            state.extra["k"] = k
        else:
            new_k = radius + k_step
            state.extra["k"] = min(new_k, k_max) if k_max is not None else new_k
        return cand

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=BetterAcceptance(),
        stop=stop,
        record_history=record_history,
    )


def run_local_branching(skeleton: TrajectorySkeleton, inst, rng: Random) -> RunResult:
    return skeleton.run(inst, rng, initial_extra={"_inst": inst})
