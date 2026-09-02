"""Fix-and-Optimize (§5.2/§5.3) = LNS-MIP con destrucción *estructurada por bloques*.

    sol ← CONSTRUCTOR(inst)                # típicamente Relax-and-Fix
    blocks ← POLITICA.blocks(P.variable_groups(inst), block_size)
    mientras no PARADA():
        free ← siguiente bloque (orden secuencial o aleatorio)
        cand ← model.solve(fijar todo salvo free, enteras free)
        si ACEPTACION(f(sol), f(cand)): sol ← cand

Mismo `TrajectorySkeleton`; lo único propio es el `candidate_generator`
que recorre los bloques y guarda el índice en `state.extra`.
"""

from __future__ import annotations

from random import Random

from core.contracts import Acceptance, Constructor, FixingPolicy, ProblemModel, StopCriterion
from core.skeleton import RunResult, SearchState, TrajectorySkeleton


def build_fix_and_optimize(
    problem: ProblemModel,
    constructor: Constructor,
    fixing_policy: FixingPolicy,
    acceptance: Acceptance,
    stop: StopCriterion,
    block_size: int = 2,
    time_limit: float = 5.0,
    order: str = "sequential",  # "sequential" | "random"
    record_history: bool = False,
) -> TrajectorySkeleton:
    def candidate_generator(sol, state: SearchState, rng: Random):
        if "mip_model" not in state.extra:
            inst = state.extra["_inst"]
            state.extra["mip_model"] = problem.build_mip(inst)
            state.extra["blocks"] = fixing_policy.blocks(problem.variable_groups(inst), block_size)
            state.extra["block_idx"] = 0
        model = state.extra["mip_model"]
        blocks = state.extra["blocks"]

        if order == "random":
            free = rng.choice(blocks)
        else:
            free = blocks[state.extra["block_idx"] % len(blocks)]
            state.extra["block_idx"] += 1

        assignment = problem.to_assignment(sol)
        fixed = {v: val for v, val in assignment.items() if v not in free}
        x = model.solve(fixed=fixed, integer=set(free), relaxed=set(), time_limit=time_limit, warm_start=assignment)
        return None if x is None else problem.from_assignment(x)

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=acceptance,
        stop=stop,
        record_history=record_history,
    )


def run_fix_and_optimize(skeleton: TrajectorySkeleton, inst, rng: Random) -> RunResult:
    return skeleton.run(inst, rng, initial_extra={"_inst": inst})
