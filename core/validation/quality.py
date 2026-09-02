"""Capa 5 — calidad mínima (§7): filtro barato para descartar variantes
inertes antes del tuning caro. La variante debe mejorar al constructor
aleatorio de referencia (`ctx.baseline_constructor`) en la mayoría de
las micro-instancias, y sus mejores soluciones no deben ser todas
idénticas a la inicial (diversidad mínima).
"""

from __future__ import annotations

from random import Random
from statistics import mean

from .base import CheckResult, ValidationContext, fail, ok
from .operational import VariantRunner

LAYER = "quality"


def check_min_quality(
    runner: VariantRunner,
    ctx: ValidationContext,
    budget_seconds: float = 2.0,
    min_relative_improvement: float = 0.0,
    majority: float = 0.5,
) -> list[CheckResult]:
    if ctx.baseline_constructor is None:
        return [ok(LAYER, "skipped", "sin baseline_constructor en el contexto")]
    wins, details, moved = 0, [], 0
    for k, inst in enumerate(ctx.instances):
        baseline = mean(ctx.problem.objective(ctx.baseline_constructor.build(inst, Random(s))) for s in ctx.seeds)
        result = runner(inst, Random(ctx.seeds[0]), budget_seconds)
        start = ctx.problem.objective(ctx.baseline_constructor.build(inst, Random(ctx.seeds[0])))
        if result.best_objective != start:
            moved += 1
        improvement = (baseline - result.best_objective) / max(1.0, abs(baseline))
        details.append(f"inst_{k}: baseline={baseline:.4g} variante={result.best_objective:.4g} ({improvement:+.1%})")
        if improvement > min_relative_improvement:
            wins += 1
    n = len(ctx.instances)
    results = []
    if wins / n >= majority:
        results.append(ok(LAYER, "improves_over_baseline", f"{wins}/{n}: " + "; ".join(details)))
    else:
        results.append(fail(LAYER, "improves_over_baseline", f"solo mejora al constructor aleatorio en {wins}/{n} micro-instancias: " + "; ".join(details)))
    if moved == 0:
        results.append(fail(LAYER, "not_inert", "la mejor solución coincide con la inicial en todas las micro-instancias: la variante no se mueve"))
    else:
        results.append(ok(LAYER, "not_inert"))
    return results
