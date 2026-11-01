"""HYB: matheurística híbrida, búsqueda local rápida alternada con sub-MIPs (LNS-MIP sobre ILS).

    s ← CONSTRUCTOR
    mientras quede tiempo:
        s ← ILS desde s durante HYB.ls_share del presupuesto (en C++ con el backend nativo)
        partial, free ← DESTROY(s, HYB.destroy_ratio)
        s' ← sub-MIP con las variables de `free` libres y el resto fijo en s, warm start s, HYB.mip_share del presupuesto
        si f(s') <= f(s): s ← s'

La búsqueda local encuentra rápido buenas soluciones; el MIP reoptimiza de forma exacta una parte de la solución, con
las restricciones y el costo completos (en el CLSP, cuándo hacer setup y cuánto producir a la vez), y puede salir de
óptimos locales que ningún movimiento alcanza. Nada del problema: la destrucción y el MIP son los del catálogo y del
`ProblemModel` (`build_mip`, `to_assignment`, `from_assignment`).
"""

from __future__ import annotations

import time
from random import Random
from typing import Any, Callable

from core.skeleton import RunResult

# local_search(sol | None, seconds, rng) -> (solución, objetivo, iteraciones); con None parte del constructor
LocalSearch = Callable[[Any, float, Random], tuple[Any, float, int]]


def run_hybrid(problem, local_search: LocalSearch, destruction, repair_mip, inst, rng: Random, budget: float,
               ls_share: float = 0.2, mip_share: float = 0.05, destroy_ratio: float = 0.2) -> RunResult:
    t0 = time.monotonic()
    left = lambda: budget - (time.monotonic() - t0)  # noqa: E731
    mip = problem.build_mip(inst)
    sol, _, iters = local_search(None, min(left(), budget * ls_share), rng)
    f = problem.objective(sol)  # el objetivo del ProblemModel (la búsqueda puede ponderar distinto las violaciones)
    best, f_best = (sol, f) if problem.is_feasible(sol) else (None, float("inf"))
    while left() > 0.05:
        _partial, free = destruction.destroy(sol, destroy_ratio, rng)
        full = problem.to_assignment(sol)
        fixed = {v: x for v, x in full.items() if v not in free}
        cand = repair_mip.repair_mip(mip, fixed, free, time_limit=max(0.1, min(left(), budget * mip_share)), warm_start=full)
        if cand is not None:
            fc = problem.objective(cand)
            if fc <= f:
                sol, f = cand, fc
                if f < f_best and problem.is_feasible(sol):
                    best, f_best = sol, f
        if left() <= 0.05:
            break
        sol, _, k = local_search(sol, min(left(), budget * ls_share), rng)
        f = problem.objective(sol)
        iters += k + 1
        if f < f_best and problem.is_feasible(sol):
            best, f_best = sol, f
    if best is None:
        best, f_best = sol, problem.objective(sol)
    return RunResult(best_solution=best, best_objective=f_best, iterations=iters, elapsed_time=time.monotonic() - t0,
                     accepted=0)
