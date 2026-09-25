"""Capa 5 — calidad mínima (§7): filtro barato para descartar variantes
inertes antes del tuning caro. La variante debe mejorar al constructor
aleatorio de referencia (`ctx.baseline_constructor`) en la mayoría de
las micro-instancias, y sus mejores soluciones no deben ser todas
idénticas a la inicial (diversidad mínima).
"""

from __future__ import annotations

from dataclasses import replace
from random import Random
from statistics import mean

from .base import CheckResult, ValidationContext, fail, ok
from .diversity import most_similar, novelty_of_improvements
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


def _reference_improvements(ctx: ValidationContext, k: int = 0, top: int = 3) -> str:
    """Si el contexto trae un vecindario de referencia, lista movimientos que SÍ mejoran desde la
    partida: la verdad-terreno que el LLM necesita para no adivinar (§6, feedback concreto)."""
    ref = ctx.reference_neighborhood
    if ref is None:
        return ""
    try:
        sol = ctx.trivial_solutions[k]
        deltas = sorted((ref.delta(sol, m), m) for m in ref.moves(sol))
        good = [(d, m) for d, m in deltas if d < -ctx.tolerance][:top]
        if not good:
            return ""
        desc = getattr(ref, "describe_move", None)
        items = [f"{(desc(sol, m) if desc else repr(m))} (Δ={d:.0f})" for d, m in good]
        return " Para que veas qué SÍ mejora desde esa partida en la micro-instancia 0: " + "; ".join(items) + "."
    except Exception:  # noqa: BLE001
        return ""


def hint(problem, key: str) -> str:
    """Sugerencia propia del problema para un mensaje del validador (`validation_hints` del
    `ProblemModel`), con un espacio adelante; "" si el problema no la trae. El texto de los
    mensajes es genérico: lo que depende del problema (qué movimiento mejora, qué hace
    infactible a un constructor) lo aporta el problema."""
    text = (getattr(problem, "validation_hints", None) or {}).get(key, "")
    return f" {text}" if text else ""


_WHAT = {
    "neighborhood": "los vecinos alcanzables desde la misma solución",
    "destruction": "la forma de los conjuntos que libera (tamaño, concentración y contigüidad por coordenada de las variables)",
    "perturbation": "la forma del conjunto de variables que cambia (cuántas, concentración por coordenada, si enciende o apaga)",
    "greedy_score": "las acciones que elige el constructor greedy al construir la misma instancia",
}


def diversity_check(
    slot: str, impl, peers: list, sol, problem=None, max_similarity: float = 0.8, min_novelty: float = 0.25
) -> list[CheckResult]:
    """Rechaza un componente estructuralmente equivalente a otro ya aceptado del mismo slot."""
    if not peers:
        return []
    sim = most_similar(slot, impl, peers, sol, problem)
    if sim is None:
        return []
    name, j = sim
    results = _similarity_result(slot, name, j, max_similarity, problem)
    if slot == "neighborhood" and problem is not None and all(r.passed for r in results):
        results += _novelty_result(impl, peers, sol, problem, min_novelty)
    return results


def _novelty_result(impl, peers, sol, problem, min_novelty: float) -> list[CheckResult]:
    novel, total, per_peer = novelty_of_improvements(impl, peers, sol, problem)
    if total == 0:
        return []  # sin mejoras desde la partida: eso lo juzga `improves_from_start`, no este gate
    share = novel / total
    if share >= min_novelty:
        return [ok(LAYER, "neighborhood.novel_improvements", f"{novel}/{total} mejoras desde la partida no las alcanza ningún par")]
    worst = max(per_peer, key=per_peer.get)
    return [fail(LAYER, "neighborhood.novel_improvements",
        f"de tus {total} movimientos que MEJORAN desde la solución de partida, {total - novel} llegan a vecinos que "
        f"`{worst}` (ya aceptado) también alcanza; solo {novel} son nuevos ({share:.0%}, se exige al menos {min_novelty:.0%}). "
        f"Es decir: lo que aporta este operador es lo mismo que aporta `{worst}`, y lo que agregaste distinto de él NO mejora "
        f"desde la partida. Agregar los movimientos de `{worst}` a otro operador para pasar `improves_from_start` no cuenta "
        f"como idea nueva. Busca movimientos que mejoren y que `{worst}` no pueda hacer en un paso.{hint(problem, 'novelty')}")]


def _similarity_result(slot: str, name: str, j: float, max_similarity: float, problem=None) -> list[CheckResult]:
    if j > max_similarity:
        return [fail(LAYER, f"{slot}.distinct_from_accepted",
            f"produce esencialmente los mismos resultados que `{name}`, ya aceptado "
            f"(similitud {j:.2f} sobre {_WHAT.get(slot, 'lo que produce')}; se tolera hasta {max_similarity:.2f}). "
            f"No basta con otro nombre ni otra representación del movimiento: hace falta una IDEA "
            f"algorítmica distinta, que alcance soluciones que `{name}` no alcanza. "
            f"Ejes por los que variar: cuántas variables toca a la vez, qué parte de la estructura del problema usa, "
            f"sobre qué unidad opera.{hint(problem, 'distinct')}")]
    return [ok(LAYER, f"{slot}.distinct_from_accepted", f"más parecido: `{name}` con similitud {j:.2f}")]


def probe_checks(slot: str, impl, probe) -> list[CheckResult]:
    """Propiedades que las micro-instancias no pueden juzgar y la sonda grande sí.

    Constructor: `constructor.feasible` se comprueba en las micro-instancias. Un greedy puede
    ser factible allí e infactible en tamaño realista (CLSP: factible con 3 ítems, faltante
    con 10): la factibilidad de un constructor es una propiedad de tamaño realista.
    """
    P = probe.problem
    inst = getattr(P, "inst", None)
    if slot == "destruction":
        n_lo = [len(impl.destroy(probe.solution, 0.1, Random(s))[1]) for s in (0, 1, 2)]
        n_hi = [len(impl.destroy(probe.solution, 0.5, Random(s))[1]) for s in (0, 1, 2)]
        if mean(n_hi) <= mean(n_lo):
            return [fail(LAYER, "destruction.ratio_monotone",
                         f"en la instancia de tamaño realista, |free_vars| con ratio=0.5 ({mean(n_hi):.1f}) no supera a ratio=0.1 ({mean(n_lo):.1f})")]
        return [ok(LAYER, "destruction.ratio_monotone", f"|free_vars|: ratio 0.1 → {mean(n_lo):.1f}, ratio 0.5 → {mean(n_hi):.1f}")]
    if slot == "greedy_score":  # un puntaje se juzga por el constructor greedy que arma
        from core.construction import GreedyConstructor

        impl, slot = GreedyConstructor(P, impl), "constructor"
    if slot != "constructor" or inst is None:
        return []
    explain = getattr(P, "explain_infeasibility", None)
    for seed in (0, 1, 2):
        try:
            sol = impl.build(inst, Random(seed))
        except Exception as exc:  # noqa: BLE001
            return [fail(LAYER, "constructor.feasible_on_probe", f"build() lanzó {type(exc).__name__} en la instancia grande: {exc}")]
        if not P.is_feasible(sol):
            why = ""
            if explain is not None:
                try:
                    why = " Detalle: " + explain(sol)
                except Exception:  # noqa: BLE001
                    why = ""
            return [fail(LAYER, "constructor.feasible_on_probe",
                f"factible en las micro-instancias pero NO en la instancia de tamaño realista (seed={seed})."
                f"{hint(P, 'constructor_probe')}{why}")]
    return [ok(LAYER, "constructor.feasible_on_probe", "factible en la instancia grande con 3 semillas")]


def random_solutions(P, inst, seeds, variables) -> list:
    """Soluciones "al azar" para probar un vecindario lejos de la partida. Si el ProblemModel
    define `random_solution(rng)`, se usa. Si no, una asignación 0/1 al azar leída con
    `from_assignment`: vale cuando toda asignación es una solución (matriz de setups del CLSP)
    y no cuando la estructura tiene reglas (en el CVRP, arcos al azar no forman rutas y los
    componentes fallaban con razón sobre esas "soluciones")."""
    gen = getattr(P, "random_solution", None)
    out = []
    for s in seeds:
        rng = Random(1000 + s)  # un rng por solución, no por variable
        if callable(gen):
            out.append(gen(rng))
        else:
            out.append(P.from_assignment({v: float(rng.random() < 0.5) for v in variables()}))
    return out


def _raises(fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except Exception:  # noqa: BLE001
        return True


def _short(obj, n: int = 300) -> str:
    text = repr(obj)
    return text if len(text) <= n else text[:n] + "…"


def check_component_quality(slot: str, impl, ctx: ValidationContext) -> list[CheckResult]:
    P = ctx.problem
    if slot == "greedy_score":
        # Diversidad como puntaje (qué acciones elige); calidad como el constructor que arma.
        from core.construction import GreedyConstructor

        results = [] if ctx.diversity_probe is not None else list(
            diversity_check(slot, impl, ctx.accepted_peers, ctx.trivial_solutions[0], P, ctx.max_similarity_to_peers))
        return results + check_component_quality("constructor", GreedyConstructor(P, impl), replace(ctx, accepted_peers=[]))
    # Si el contexto trae una sonda de diversidad, la comparación se hace allí (instancia
    # grande, componente reconstruido) desde `llm.generator`, no aquí con la micro-instancia.
    results: list[CheckResult] = [] if ctx.diversity_probe is not None else list(
        diversity_check(slot, impl, ctx.accepted_peers, ctx.trivial_solutions[0], ctx.problem, ctx.max_similarity_to_peers)
    )

    if slot == "constructor":
        # No absurdamente peor que la solución trivial factible de referencia. Umbral laxo
        # a propósito: la referencia puede ser Relax-and-Fix (MIP) y un constructor solo
        # tiene que ser un punto de partida usable, no competir con una matheurística.
        limit = ctx.constructor_max_relative_gap
        worst_ratio, worst_k = 0.0, 0
        for k, inst in enumerate(ctx.instances):
            f_triv = P.objective(ctx.trivial_solutions[k])
            f_built = mean(P.objective(impl.build(inst, Random(s))) for s in ctx.seeds)
            ratio = (f_built - f_triv) / max(1.0, abs(f_triv))
            if ratio > worst_ratio:
                worst_ratio, worst_k = ratio, k
        if worst_ratio > limit:
            f_triv = P.objective(ctx.trivial_solutions[worst_k])
            results.append(fail(LAYER, "constructor.not_much_worse_than_trivial",
                f"el constructor cuesta {worst_ratio:+.0%} más que la solución de referencia en la micro-instancia {worst_k} "
                f"(referencia = {f_triv:.0f}; umbral tolerado {limit:+.0%}). No hace falta que sea óptimo, pero sí un punto de "
                f"partida razonable.{hint(P, 'constructor_quality')}"))
        else:
            results.append(ok(LAYER, "constructor.not_much_worse_than_trivial", f"peor caso {worst_ratio:+.0%} vs referencia (límite {limit:+.0%})"))

    elif slot == "neighborhood":
        # Debe existir al menos un movimiento de mejora. Se distingue entre soluciones de
        # PARTIDA (trivial + constructor base: donde el esqueleto arranca de verdad) y
        # soluciones aleatorias (estados intermedios de una búsqueda).
        imp_start, tot_start, imp_rand, tot_rand = 0, 0, 0, 0
        for k in range(len(ctx.instances)):
            start = [ctx.trivial_solutions[k]]
            if ctx.baseline_constructor is not None:
                start += [ctx.baseline_constructor.build(ctx.instances[k], Random(s)) for s in ctx.seeds[:2]]
            rand = random_solutions(P, ctx.instances[k], ctx.seeds[:3], lambda: sorted(ctx.variables(ctx.instances[k])))
            for group, sols in (("start", start), ("rand", rand)):
                for sol in sols:
                    moves = list(impl.moves(sol))
                    sample = moves if len(moves) <= ctx.max_moves_checked else Random(0).sample(moves, ctx.max_moves_checked)
                    try:
                        imp = sum(1 for m in sample if impl.delta(sol, m) < -ctx.tolerance)
                    except Exception as exc:  # noqa: BLE001 — con el movimiento y la solución, el LLM puede corregirlo
                        bad = next(m for m in sample if _raises(impl.delta, sol, m))
                        results.append(fail(LAYER, "neighborhood.delta_runs",
                            f"delta(sol, m={bad!r}) lanzó {type(exc).__name__}: {exc}. m salió de moves(sol) con "
                            f"sol={_short(sol)} ({'solución de partida' if group == 'start' else 'solución al azar'})."))
                        return results
                    if group == "start":
                        tot_start += len(moves); imp_start += imp
                    else:
                        tot_rand += len(moves); imp_rand += imp
        if tot_start + tot_rand == 0:
            results.append(fail(LAYER, "neighborhood.has_improving_move", "moves() vacío en todas las soluciones de prueba"))
        elif imp_start + imp_rand == 0:
            results.append(fail(LAYER, "neighborhood.has_improving_move", f"ninguno de los {tot_start + tot_rand} movimientos muestreados mejora la solución en ninguna micro-instancia: vecindario inerte"))
        elif imp_start == 0 and ctx.require_improving_from_start:
            ref_hint = _reference_improvements(ctx)
            results.append(fail(LAYER, "neighborhood.improves_from_start",
                f"desde la solución de PARTIDA (la que produce el constructor de partida del esqueleto) moves() devuelve "
                f"{tot_start} movimientos y NINGUNO mejora; solo hay mejoras ({imp_rand}) desde soluciones aleatorias. "
                f"El esqueleto arranca en la solución de partida, así que este vecindario lo deja inmóvil.{ref_hint} "
                f"NO compliques el operador con movimientos compuestos para lograrlo: mantén `undo` exacto y `moves()` simple; "
                f"un movimiento elemental correcto que mejore vale más que uno sofisticado que rompa las propiedades ya aprobadas."))
        else:
            results.append(ok(LAYER, "neighborhood.has_improving_move",
                f"{imp_start} mejoras desde soluciones de partida, {imp_rand} desde aleatorias"))

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
        # Con sonda, este chequeo se hace allí (`probe_checks`, en tamaño realista): en una
        # micro-instancia (6 clientes) el redondeo y los tamaños mínimos legítimos empatan 0.1 y 0.5.
        if ctx.diversity_probe is not None:
            return results
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
