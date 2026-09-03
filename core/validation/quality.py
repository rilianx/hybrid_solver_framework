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


# --------------------------------------------------------------------------- calidad por componente
#
# Las propiedades contractuales detectan errores de *implementación* (undo mal
# hecho, delta con signo cambiado). Estas verifican que el componente tenga
# *sentido* como pieza de búsqueda, con umbrales deliberadamente laxos: no
# pretenden elegir el mejor componente (eso es el tuning), sino descartar los
# que no pueden aportar nada.


def _hamming(problem, a, b) -> int:
    xa, xb = problem.to_assignment(a), problem.to_assignment(b)
    return sum(1 for k in xa if abs(xa[k] - xb.get(k, xa[k])) > 1e-9)


def check_component_quality(slot: str, impl, ctx: ValidationContext) -> list[CheckResult]:
    P = ctx.problem
    results: list[CheckResult] = []

    if slot == "constructor":
        # No mucho peor que la solución trivial factible que ya conocemos.
        worst_ratio = 0.0
        for k, inst in enumerate(ctx.instances):
            f_triv = P.objective(ctx.trivial_solutions[k])
            f_built = mean(P.objective(impl.build(inst, Random(s))) for s in ctx.seeds)
            worst_ratio = max(worst_ratio, (f_built - f_triv) / max(1.0, abs(f_triv)))
        if worst_ratio > 0.25:
            results.append(fail(LAYER, "constructor.not_much_worse_than_trivial", f"el constructor es {worst_ratio:+.0%} peor que la solución trivial factible en alguna micro-instancia (umbral +25%)"))
        else:
            results.append(ok(LAYER, "constructor.not_much_worse_than_trivial", f"peor caso {worst_ratio:+.0%} vs trivial"))

    elif slot == "neighborhood":
        # Debe existir al menos un movimiento de mejora desde alguna solución típica;
        # un vecindario sin mejoras posibles es inerte para cualquier esqueleto.
        improving, total = 0, 0
        for k in range(len(ctx.instances)):
            sols = [ctx.trivial_solutions[k]]
            if ctx.baseline_constructor is not None:
                sols += [ctx.baseline_constructor.build(ctx.instances[k], Random(s)) for s in ctx.seeds[:2]]
            # soluciones aleatorias (vista MIP → estructural): un vecindario puede ser
            # inútil desde la solución trivial y aun así tener mejoras desde estados típicos
            # de una búsqueda; ver p.ej. "mover setup al período anterior".
            names = sorted(ctx.variables(ctx.instances[k]))
            for s in ctx.seeds[:3]:
                rng = Random(1000 + s)
                sols.append(P.from_assignment({v: float(rng.random() < 0.5) for v in names}))
            for sol in sols:
                moves = list(impl.moves(sol))
                total += len(moves)
                sample = moves if len(moves) <= ctx.max_moves_checked else Random(0).sample(moves, ctx.max_moves_checked)
                improving += sum(1 for m in sample if impl.delta(sol, m) < -ctx.tolerance)
        if total == 0:
            results.append(fail(LAYER, "neighborhood.has_improving_move", "moves() vacío en todas las soluciones de prueba"))
        elif improving == 0:
            results.append(fail(LAYER, "neighborhood.has_improving_move", f"ninguno de los {total} movimientos muestreados mejora la solución en ninguna micro-instancia: vecindario inerte"))
        else:
            results.append(ok(LAYER, "neighborhood.has_improving_move", f"{improving} movimientos de mejora encontrados"))

    elif slot == "perturbation":
        # `strength` debe significar algo: más fuerza, más distancia (Hamming en la vista MIP).
        d1, d3 = [], []
        for k in range(len(ctx.instances)):
            sol = ctx.trivial_solutions[k]
            d1 += [_hamming(P, sol, impl.perturb(sol, 1.0, Random(s))) for s in ctx.seeds]
            d3 += [_hamming(P, sol, impl.perturb(sol, 3.0, Random(s))) for s in ctx.seeds]
        if mean(d3) < mean(d1):
            results.append(fail(LAYER, "perturbation.strength_monotone", f"distancia media con strength=3 ({mean(d3):.1f}) menor que con strength=1 ({mean(d1):.1f})"))
        else:
            results.append(ok(LAYER, "perturbation.strength_monotone", f"Hamming medio: strength 1 → {mean(d1):.1f}, strength 3 → {mean(d3):.1f}"))

    elif slot == "destruction":
        # `ratio` debe significar algo: más ratio, más variables liberadas.
        n_lo, n_hi = [], []
        for k in range(len(ctx.instances)):
            sol = ctx.trivial_solutions[k]
            n_lo += [len(impl.destroy(sol, 0.1, Random(s))[1]) for s in ctx.seeds]
            n_hi += [len(impl.destroy(sol, 0.5, Random(s))[1]) for s in ctx.seeds]
        if mean(n_hi) <= mean(n_lo):
            results.append(fail(LAYER, "destruction.ratio_monotone", f"|free_vars| con ratio=0.5 ({mean(n_hi):.1f}) no supera a ratio=0.1 ({mean(n_lo):.1f})"))
        else:
            results.append(ok(LAYER, "destruction.ratio_monotone", f"|free_vars|: ratio 0.1 → {mean(n_lo):.1f}, ratio 0.5 → {mean(n_hi):.1f}"))

    return results
