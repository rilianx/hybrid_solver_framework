"""Equivalencia de una versión optimizada contra la aceptada (el oráculo) y su aceleración.

La etapa de optimización (`llm.optimizer`) le pide al LLM una versión más rápida de un modelo
por piezas o de un componente ya aceptados. Lo aceptado es el oráculo: la versión nueva tiene
que dar las mismas salidas en las mismas entradas (pruebas diferenciales), y además ser más
rápida de verdad. Así una optimización no puede cambiar el comportamiento, solo la velocidad.
"""

from __future__ import annotations

import itertools
import math
import time
from random import Random
from typing import Any, Callable

from core.model_parts import CONSTRUCTION_PARTS, MIP_PARTS, TOL, has_construction

from .base import ValidationReport, fail, ok, describe_exception

LAYER = "equivalence"


def _close(a: float, b: float, tol: float = 1e-6) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol * 100)


def _short(obj, n: int = 200) -> str:
    text = repr(obj)
    return text if len(text) <= n else text[:n] + "…"


def _viol(parts, inst, sol) -> dict[str, float]:
    return {k: float(v) for k, v in parts.violations(inst, sol).items() if float(v) > TOL}


def _dict_close(a: dict, b: dict) -> bool:
    return set(a) == set(b) and all(_close(a[k], b[k]) for k in a)


def rate(fn: Callable[[], Any], seconds: float = 0.5, max_calls: int = 200_000) -> float:
    """Llamadas por segundo de `fn`."""
    t0, n = time.perf_counter(), 0
    while n < max_calls and time.perf_counter() - t0 < seconds:
        fn()
        n += 1
    return n / max(time.perf_counter() - t0, 1e-9)


# ---------------------------------------------------------------- modelo por piezas
def parts_test_solutions(parts, inst, cases_answers: list, n_random: int = 30) -> list:
    sols = [parts.trivial_solution(inst)] + [parts.random_solution(inst, Random(s)) for s in range(n_random)]
    sols += [parts.from_answer(inst, a) for a in cases_answers]
    return sols


def check_parts_equivalent(old, new, instances: list[tuple[Any, list]], n_random: int = 30) -> ValidationReport:
    """`instances`: [(instancia, respuestas de casos)]. Las mismas salidas en la vista heurística, la
    vista MIP (datos y puente) y la vista constructiva (reproduciendo construcciones al azar)."""
    report = ValidationReport(subject="equivalencia del modelo")
    for k, (inst, answers) in enumerate(instances):
        where = f"instancia {k}"
        try:
            sols = parts_test_solutions(old, inst, answers, n_random)
            for fn in ("trivial_solution",):
                if getattr(old, fn)(inst) != getattr(new, fn)(inst):
                    report.add(fail(LAYER, f"{fn}_equal", f"{fn} cambió en {where}"))
                    return report
            for s in range(3):
                if old.random_solution(inst, Random(s)) != new.random_solution(inst, Random(s)):
                    report.add(fail(LAYER, "random_solution_equal", f"random_solution(rng) cambió con la misma semilla en {where}"))
                    return report
            for a in answers:
                if old.from_answer(inst, a) != new.from_answer(inst, a):
                    report.add(fail(LAYER, "from_answer_equal", f"from_answer cambió para la respuesta {_short(a)} en {where}"))
                    return report
            for sol in sols:
                if new.canonical(sol) != old.canonical(sol):
                    report.add(fail(LAYER, "canonical_equal", f"canonical cambió para {_short(sol)} en {where}"))
                    return report
                vo, vn = _viol(old, inst, sol), _viol(new, inst, sol)
                if not _dict_close(vo, vn):
                    report.add(fail(LAYER, "violations_equal", f"violations cambió en {where}: antes {vo}, ahora {vn}, sol={_short(sol)}"))
                    return report
                co, cn = old.cost_terms(inst, sol), new.cost_terms(inst, sol)
                if not _dict_close(co, cn):
                    report.add(fail(LAYER, "cost_terms_equal", f"cost_terms cambió en {where}: antes {co}, ahora {cn}, sol={_short(sol)}"))
                    return report
            if all(callable(getattr(old, n, None)) for n in MIP_PARTS):
                for fn in ("variables", "structural_variables", "constraint_families", "objective_terms", "variable_groups"):
                    if repr(getattr(old, fn)(inst)) != repr(getattr(new, fn)(inst)):
                        report.add(fail(LAYER, f"{fn}_equal", f"{fn} cambió en {where}"))
                        return report
                for sol in sols:
                    if not _viol(old, inst, sol):
                        if old.to_assignment(inst, sol) != new.to_assignment(inst, sol):
                            report.add(fail(LAYER, "to_assignment_equal", f"to_assignment cambió en {where}, sol={_short(sol)}"))
                            return report
                        if not _dict_close(old.aux_values(inst, sol), new.aux_values(inst, sol)):
                            report.add(fail(LAYER, "aux_values_equal", f"aux_values cambió en {where}, sol={_short(sol)}"))
                            return report
            if has_construction(old):
                if not has_construction(new):
                    report.add(fail(LAYER, "construction_kept", f"la versión nueva no tiene las funciones {CONSTRUCTION_PARTS}"))
                    return report
                bad = _replay_construction(old, new, inst)
                if bad:
                    report.add(fail(LAYER, "construction_equal", f"la vista constructiva cambió en {where}: {bad}"))
                    return report
        except Exception as exc:  # noqa: BLE001
            report.add(fail(LAYER, "runs", f"la versión nueva lanzó {describe_exception(exc)} en {where}"))
            return report
    report.add(ok(LAYER, "same_outputs", f"mismas salidas en {len(instances)} instancias"))
    return report


def _replay_construction(old, new, inst, n: int = 3, max_steps: int = 20_000) -> str | None:
    for s in range(n):
        rng = Random(s)
        po, pn = old.empty_partial(inst), new.empty_partial(inst)
        for _ in range(max_steps):
            do, dn = old.is_complete(inst, po), new.is_complete(inst, pn)
            if do != dn:
                return "is_complete difiere"
            if do:
                if old.to_solution(inst, po) != new.to_solution(inst, pn):
                    return "to_solution difiere"
                break
            co, cn = list(old.candidates(inst, po)), list(new.candidates(inst, pn))
            if repr(co) != repr(cn):
                return f"candidates difiere: antes {_short(co)}, ahora {_short(cn)}"
            if not co:
                break
            k = rng.randrange(len(co))
            po, pn = old.apply_action(inst, po, co[k]), new.apply_action(inst, pn, cn[k])
    return None


def parts_speed(parts, inst, n: int = 2000, seconds: float = 0.5) -> float:
    """Evaluaciones por segundo de violations + cost_terms en soluciones distintas (sin caché)."""
    sols = [parts.random_solution(inst, Random(10_000 + s)) for s in range(n)]
    it = itertools.cycle(sols)

    def one():
        sol = next(it)
        parts.violations(inst, sol)
        parts.cost_terms(inst, sol)

    return rate(one, seconds, n)


def _construct(parts, inst, rng: Random, max_steps: int = 20_000):
    p = parts.empty_partial(inst)
    for _ in range(max_steps):
        if parts.is_complete(inst, p):
            return parts.to_solution(inst, p)
        cands = list(parts.candidates(inst, p))
        if not cands:
            return parts.complete_partial(inst, p, rng)
        p = parts.apply_action(inst, p, cands[rng.randrange(len(cands))])
    return None


def constructive_workload_speed(parts, inst, seconds: float = 3.0, n_constructions: int = 2, n_evals: int = 200) -> float:
    """Unidades de trabajo por segundo en un modelo SIN vista MIP, que las heurísticas usan solo por el
    lado constructivo: una unidad = `trivial_solution` + `n_constructions` construcciones al azar +
    `n_evals` evaluaciones (violations + cost_terms). En el CPMP de la corrida 61 las evaluaciones
    eran baratas y lo lento era la búsqueda de `trivial_solution`, que usa también el respaldo de la
    vista: medir solo evaluaciones no veía el cuello de botella."""
    sols = [parts.random_solution(inst, Random(10_000 + s)) for s in range(n_evals)]
    state = {"k": 0}

    def one():
        k = state["k"]
        state["k"] += 1
        parts.trivial_solution(inst)
        for c in range(n_constructions):
            _construct(parts, inst, Random(1000 * k + c))
        for sol in sols:
            parts.violations(inst, sol)
            parts.cost_terms(inst, sol)

    return rate(one, seconds, 1000)


def parts_profile(parts, inst) -> dict[str, float]:
    """Segundos por pieza en una instancia de tamaño realista, para decirle al LLM dónde está el tiempo."""
    import time

    out: dict[str, float] = {}
    t0 = time.perf_counter()
    parts.trivial_solution(inst)
    out["trivial_solution (s)"] = time.perf_counter() - t0
    if has_construction(parts):
        t0 = time.perf_counter()
        _construct(parts, inst, Random(0))
        out["una construcción al azar, con complete_partial si hace falta (s)"] = time.perf_counter() - t0
    sols = [parts.random_solution(inst, Random(10_000 + s)) for s in range(200)]
    t0 = time.perf_counter()
    for sol in sols:
        parts.violations(inst, sol)
        parts.cost_terms(inst, sol)
    out["200 evaluaciones violations + cost_terms (s)"] = time.perf_counter() - t0
    return out


def model_speed(parts, inst) -> tuple[float, str]:
    """(velocidad, unidad) con la que se optimiza un modelo: evaluaciones por segundo si tiene vista
    MIP (las heurísticas de trayectoria lo evalúan millones de veces), unidades de trabajo
    constructivo por segundo si no la tiene."""
    if not all(callable(getattr(parts, n, None)) for n in MIP_PARTS) and has_construction(parts):
        return constructive_workload_speed(parts, inst), "unidades de trabajo constructivo/s"
    return parts_speed(parts, inst), "evaluaciones/s"


# ---------------------------------------------------------------- componentes
def check_component_equivalent(slot: str, old, new, problem, sols: list, n_moves: int = 200) -> ValidationReport:
    """Mismas salidas que el componente aceptado, sobre las mismas soluciones y semillas."""
    report = ValidationReport(subject=f"equivalencia ({slot})")
    try:
        for k, sol in enumerate(sols):
            where = f"solución {k}"
            if slot == "neighborhood":
                mo = list(itertools.islice(old.moves(sol), n_moves))
                mn = list(itertools.islice(new.moves(sol), n_moves))
                if repr(mo) != repr(mn):
                    report.add(fail(LAYER, "moves_equal", f"moves(sol) cambió en {where}: antes {_short(mo)}, ahora {_short(mn)}"))
                    return report
                for m in mo[:50]:
                    ao, an = old.apply(sol, m), new.apply(sol, m)
                    if ao != an:
                        report.add(fail(LAYER, "apply_equal", f"apply(sol, {_short(m)}) cambió en {where}"))
                        return report
                    if not _close(old.delta(sol, m), new.delta(sol, m)):
                        report.add(fail(LAYER, "delta_equal", f"delta(sol, {_short(m)}) cambió en {where}: antes {old.delta(sol, m):.6g}, "
                                                              f"ahora {new.delta(sol, m):.6g}"))
                        return report
                    if callable(getattr(old, "undo", None)) and callable(getattr(new, "undo", None)) and old.undo(ao, m) != new.undo(an, m):
                        report.add(fail(LAYER, "undo_equal", f"undo(…, {_short(m)}) cambió en {where}"))
                        return report
            elif slot == "perturbation":
                for s in range(3):
                    if old.perturb(sol, 1.0, Random(s)) != new.perturb(sol, 1.0, Random(s)):
                        report.add(fail(LAYER, "perturb_equal", f"perturb con la misma semilla cambió en {where}"))
                        return report
            elif slot == "destruction":
                for s in range(3):
                    if repr(old.destroy(sol, 0.3, Random(s))) != repr(new.destroy(sol, 0.3, Random(s))):
                        report.add(fail(LAYER, "destroy_equal", f"destroy con la misma semilla cambió en {where}"))
                        return report
        if slot == "greedy_score":
            view = problem.construction_view(problem.inst)
            for s in range(3):
                rng, partial = Random(s), view.empty()
                while not view.is_complete(partial):
                    cands = list(view.candidates(partial))
                    if not cands:
                        break
                    for c in cands:
                        if not _close(old.score(partial, c), new.score(partial, c)):
                            report.add(fail(LAYER, "score_equal", f"score(partial, {_short(c)}) cambió: antes {old.score(partial, c):.6g}, "
                                                                  f"ahora {new.score(partial, c):.6g}"))
                            return report
                    partial = view.apply(partial, cands[rng.randrange(len(cands))])
    except Exception as exc:  # noqa: BLE001
        report.add(fail(LAYER, "runs", f"la versión nueva lanzó {describe_exception(exc)}"))
        return report
    report.add(ok(LAYER, "same_outputs", f"mismas salidas en {len(sols)} soluciones"))
    return report


def component_speed(slot: str, make, problem_factory, inst, sol, seconds: float = 1.0) -> float:
    """La operación que el esqueleto repite, sobre un modelo NUEVO (PartsModel memoriza el objetivo por
    solución y repetir lo mismo mediría la caché): delta sobre movimientos distintos de un vecindario,
    construcciones greedy completas, perturb o destroy. `make(problem)` construye el componente."""
    problem = problem_factory(inst)
    impl = make(problem)
    t0, n = time.perf_counter(), 0
    if slot == "neighborhood":
        for m in itertools.islice(impl.moves(sol), 2000):
            impl.delta(sol, m)
            n += 1
            if time.perf_counter() - t0 > seconds:
                break
    elif slot == "greedy_score":
        from core.construction import GreedyConstructor

        while time.perf_counter() - t0 < seconds and n < 50:
            GreedyConstructor(problem_factory(inst), make(problem)).build(inst, Random(n))
            n += 1
    elif slot in ("perturbation", "destruction"):
        rng = Random(0)
        while time.perf_counter() - t0 < seconds and n < 100_000:
            impl.perturb(sol, 1.0, rng) if slot == "perturbation" else impl.destroy(sol, 0.3, rng)
            n += 1
    return n / max(time.perf_counter() - t0, 1e-9)


__all__ = ["check_component_equivalent", "check_parts_equivalent", "component_speed", "constructive_workload_speed",
           "model_speed", "parts_profile", "parts_speed", "rate"]
