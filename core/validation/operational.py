"""Capa 4 — operativa (§7): el sub-MIP de un `repair_mip` respeta `time_limit`. La llamada se lanza en un hilo
*daemon* con `join(timeout)` para que un componente que se cuelga no bloquee al validador: se reporta como FAIL y el
hilo queda abandonado."""

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
