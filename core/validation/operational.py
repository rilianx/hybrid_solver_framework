"""Capa 4 — operativa (§7): la variante ensamblada corre con un presupuesto
pequeño sin excepciones ni fugas de tiempo; el sub-MIP respeta `time_limit`.

Una *variante* se representa como un `VariantRunner`:
    run(inst, rng, budget_seconds) -> RunResult
El ensamblador la construye con un `MaxTimeStop(budget_seconds)`; esta
capa mide desde afuera que el tiempo real no se desborde. La corrida se
lanza en un hilo *daemon* con `join(timeout)` para que un componente que
se cuelga (bucle infinito en `moves`, sub-solver sin límite) no bloquee
al validador: se reporta como FAIL y el hilo queda abandonado.
"""

from __future__ import annotations

import threading
import time
from random import Random
from typing import Any, Callable

from core.skeleton import RunResult

from .base import CheckResult, ValidationContext, fail, ok

LAYER = "operational"

VariantRunner = Callable[[Any, Random, float], RunResult]


def _run_with_timeout(fn: Callable[[], Any], timeout: float) -> tuple[Any, BaseException | None, bool]:
    box: dict[str, Any] = {}

    def target():
        try:
            box["result"] = fn()
        except BaseException as exc:  # noqa: BLE001
            box["error"] = exc

    th = threading.Thread(target=target, daemon=True)
    th.start()
    th.join(timeout)
    if th.is_alive():
        return None, None, True
    return box.get("result"), box.get("error"), False


def check_variant_runs(
    runner: VariantRunner,
    ctx: ValidationContext,
    budget_seconds: float = 2.0,
    overrun_tolerance: float = 0.5,
    hard_timeout_factor: float = 4.0,
) -> list[CheckResult]:
    """`overrun_tolerance`: fracción del presupuesto que se tolera de exceso
    (una iteración en curso al vencer el reloj es legítima; el doble no)."""
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        t0 = time.perf_counter()
        result, error, hung = _run_with_timeout(
            lambda inst=inst: runner(inst, Random(ctx.seeds[0]), budget_seconds),
            timeout=budget_seconds * hard_timeout_factor + 5.0,
        )
        elapsed = time.perf_counter() - t0
        if hung:
            results.append(fail(LAYER, "terminates", f"inst_{k}: la variante no terminó en {budget_seconds * hard_timeout_factor + 5.0:.0f}s con presupuesto {budget_seconds}s (¿bucle sin criterio de parada? ¿sub-solver sin time_limit?)"))
            continue
        if error is not None:
            results.append(fail(LAYER, "no_exceptions", f"inst_{k}: {type(error).__name__}: {error}"))
            continue
        results.append(ok(LAYER, "no_exceptions"))
        if result.iterations < 1:
            results.append(fail(LAYER, "makes_progress", f"inst_{k}: 0 iteraciones en {budget_seconds}s"))
        else:
            results.append(ok(LAYER, "makes_progress", f"{result.iterations} iteraciones"))
        allowed = budget_seconds * (1 + overrun_tolerance) + 1.0
        if elapsed > allowed:
            results.append(fail(LAYER, "respects_time_budget", f"inst_{k}: tardó {elapsed:.1f}s con presupuesto {budget_seconds}s (tolerado hasta {allowed:.1f}s): fuga de tiempo en algún componente"))
        else:
            results.append(ok(LAYER, "respects_time_budget", f"{elapsed:.1f}s / {budget_seconds}s"))
        if not ctx.problem.is_feasible(result.best_solution):
            results.append(fail(LAYER, "best_is_feasible", f"inst_{k}: la mejor solución devuelta es infactible"))
        else:
            results.append(ok(LAYER, "best_is_feasible"))
    return _collapse(results)


def check_repair_mip_time_limit(
    impl, ctx: ValidationContext, time_limit: float = 1.0, slack_seconds: float = 2.0
) -> list[CheckResult]:
    """El sub-MIP respeta `time_limit` (con holgura para el arranque del solver externo)."""
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        sol = ctx.trivial_solutions[k]
        model = ctx.problem.build_mip(inst)
        assignment = ctx.problem.to_assignment(sol)
        all_vars = sorted(ctx.variables(inst))
        free = set(all_vars)  # peor caso: todo libre
        t0 = time.perf_counter()
        _, error, hung = _run_with_timeout(
            lambda: impl.repair_mip(model, {}, free, time_limit, warm_start=assignment),
            timeout=time_limit + slack_seconds + 10.0,
        )
        elapsed = time.perf_counter() - t0
        if hung or elapsed > time_limit + slack_seconds:
            results.append(fail(LAYER, "repair_mip.respects_time_limit", f"inst_{k}: repair_mip tardó {elapsed:.1f}s con time_limit={time_limit}s"))
        elif error is not None:
            results.append(fail(LAYER, "repair_mip.no_exceptions", f"inst_{k}: {type(error).__name__}: {error}"))
        else:
            results.append(ok(LAYER, "repair_mip.respects_time_limit", f"{elapsed:.1f}s / {time_limit}s"))
    return _collapse(results)


def _collapse(results: list[CheckResult]) -> list[CheckResult]:
    by_name: dict[str, CheckResult] = {}
    for r in results:
        if r.name not in by_name or (not r.passed and by_name[r.name].passed):
            by_name[r.name] = r
    return list(by_name.values())
