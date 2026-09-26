"""Validación del `ProblemModel` por piezas (`core.model_parts`) contra casos de prueba.

Tres etapas, cada una contra lo ya aceptado:

1. `check_heuristic_view`: la representación (canónica, trivial factible, al azar bien
   formada), `from_answer`, `violations` y `cost_terms`, contra las respuestas conocidas de
   los casos (factible o no, qué familia se viola, costo).
2. `check_mip_view`: el puente y la vista MIP contra la vista heurística **en un punto, sin
   solver**. Para soluciones factibles, infactibles y al azar, cada familia de restricciones
   se evalúa en `to_assignment(sol) ∪ aux_values(sol)`: la familia del MIP tiene que violarse
   exactamente cuando `violations` reporta esa familia, y cada término del objetivo tiene que
   coincidir con el de `cost_terms`. El reporte nombra la familia, la restricción y el punto.
3. `check_mip_optimum`: el MIP completo con el solver, contra el óptimo esperado del caso.

Casos visibles y ocultos, como en Codeforces: los visibles se muestran en el prompt; de un
caso oculto que falla el reporte dice qué se esperaba y qué se obtuvo, sin mostrar la
instancia, para que el modelo corrija el problema y no se ajuste al caso.
"""

from __future__ import annotations

import math
from random import Random
from typing import Any

from core.model_parts import CONSTRUCTION_PARTS, HEURISTIC_PARTS, MIP_PARTS, TOL, LinearMIP, TestCase, family_of, lhs, violated

from .base import CheckResult, ValidationReport, fail, ok


MIN_GROUPS = 4
MAX_GROUP_SHARE = 1 / 3


def _close(a: float, b: float, tol: float = 1e-5) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol * 100)


def _short(obj, n: int = 240) -> str:
    text = repr(obj)
    return text if len(text) <= n else text[:n] + "…"


def _where(case: TestCase) -> str:
    return f"caso visible '{case.name}'" if case.visible else f"un caso oculto ('{case.name}')"


def _missing(parts, names) -> list[CheckResult]:
    return [fail("syntactic", f"defines_{n}", f"falta la función `{n}`") for n in names if not callable(getattr(parts, n, None))]


def _viol(parts, inst, sol) -> dict[str, float]:
    return {k: float(v) for k, v in parts.violations(inst, sol).items() if float(v) > TOL}


def check_heuristic_view(parts, cases: list[TestCase], n_random: int = 4, decoder: bool = False) -> ValidationReport:
    """`decoder`: la representación es una codificación (p.ej. gran tour + Split). from_answer puede
    dar una codificación cuya decodificación es MEJOR que la respuesta del caso, así que el costo se
    exige no peor que el esperado; y una respuesta infactible puede no ser representable (Split nunca
    arma una ruta que exceda la capacidad): si la decodificación es factible, no se exige la violación."""
    report = ValidationReport(subject="vista heurística")
    report.extend(_missing(parts, HEURISTIC_PARTS))
    if not report.passed:
        return report
    L = "heuristic"
    for case in cases:
        inst, where = case.instance, _where(case)
        try:
            triv = parts.trivial_solution(inst)
            hash(triv)
            if parts.canonical(triv) != triv:
                report.add(fail(L, "trivial_canonical", f"trivial_solution no está en forma canónica en {where}: {_short(triv)}"))
            v = _viol(parts, inst, triv)
            if v:
                report.add(fail(L, "trivial_feasible", f"trivial_solution viola {v} en {where}: {_short(triv)}"))
            sols = [parts.random_solution(inst, Random(s)) for s in range(n_random)]
            for s in sols:
                hash(s)
                c = parts.canonical(s)
                if c != s or parts.canonical(c) != c:
                    report.add(fail(L, "canonical_idempotent", f"canonical no es idempotente o random_solution no la usa: {_short(s)} -> {_short(c)}"))
                    break
            if len({repr(s) for s in sols}) == 1 and n_random > 1:
                report.add(fail(L, "random_varies", f"random_solution devuelve siempre la misma solución en {where}"))
        except Exception as exc:  # noqa: BLE001
            report.add(fail(L, "runs", f"la vista heurística lanzó {type(exc).__name__}: {exc} en {where}"))
            return report
        for k, sc in enumerate(case.solutions):
            label = f"{where}, solución {k}" + (f" (respuesta {_short(sc['answer'], 120)})" if case.visible else "")
            try:
                sol = parts.from_answer(inst, sc["answer"])
                if parts.canonical(sol) != sol:
                    report.add(fail(L, "from_answer_canonical", f"from_answer no devuelve la forma canónica en {label}"))
                v = _viol(parts, inst, sol)
                cost = sum(parts.cost_terms(inst, sol).values())
            except Exception as exc:  # noqa: BLE001
                report.add(fail(L, "runs", f"from_answer/violations/cost_terms lanzó {type(exc).__name__}: {exc} en {label}"))
                continue
            if sc["feasible"] and v:
                report.add(fail(L, "feasibility_matches_cases", f"se esperaba FACTIBLE y violations reporta {v} en {label}"))
            elif not sc["feasible"] and not v and decoder:
                pass  # la codificación no puede expresar esa infactibilidad
            elif not sc["feasible"] and not v:
                why = f" (viola {sc['violates']})" if sc.get("violates") else ""
                report.add(fail(L, "feasibility_matches_cases", f"se esperaba INFACTIBLE{why} y violations no reporta nada en {label}"))
            elif not sc["feasible"] and sc.get("violates"):
                missing = [f for f in sc["violates"] if f not in {family_of(x) for x in v}]
                if missing:
                    report.add(fail(L, "violated_family_matches_cases",
                                    f"se esperaba que se violara la familia {missing} y violations reporta {sorted(v)} en {label}"))
            if sc.get("cost") is not None and decoder:
                if cost > sc["cost"] and not _close(cost, sc["cost"]):
                    report.add(fail(L, "cost_matches_cases", f"se esperaba costo a lo sumo {sc['cost']:.6g} (la decodificación puede "
                                                            f"mejorar la respuesta, no empeorarla) y la suma de cost_terms da {cost:.6g} en {label}"))
            elif sc.get("cost") is not None and not _close(cost, sc["cost"]):
                report.add(fail(L, "cost_matches_cases", f"se esperaba costo {sc['cost']:.6g} y la suma de cost_terms da {cost:.6g} en {label}"))
    if report.passed:
        report.add(ok(L, "matches_cases", f"{sum(len(c.solutions) for c in cases)} respuestas de {len(cases)} casos"))
    return report


def check_mip_view(parts, cases: list[TestCase], n_random: int = 4, scale_instances: list | None = None,
                   decoder: bool = False) -> ValidationReport:
    """`scale_instances`: instancias de tamaño realista donde se mide la granularidad de
    `variable_groups` (en una micro-instancia de 3 períodos, 3 grupos por período es lo correcto).
    Sin ellas se mide en los casos."""
    report = ValidationReport(subject="vista MIP")
    report.extend(_missing(parts, MIP_PARTS))
    if not report.passed:
        return report
    L = "semantic_mip"
    for k, inst in enumerate(scale_instances or []):
        try:
            struct = list(parts.structural_variables(inst))
            groups = parts.variable_groups(inst)
        except Exception as exc:  # noqa: BLE001
            report.add(fail(L, "runs", f"structural_variables/variable_groups lanzó {type(exc).__name__}: {exc} en la instancia de tamaño realista"))
            return report
        report.extend(_groups(struct, groups, f"instancia de tamaño realista {k}", granularity=True))
        if not report.passed:
            return report
    for case in cases:
        inst, where = case.instance, _where(case)
        try:
            dom = parts.variables(inst)
            struct = list(parts.structural_variables(inst))
            fams = parts.constraint_families(inst)
            obj = parts.objective_terms(inst)
            groups = parts.variable_groups(inst)
        except Exception as exc:  # noqa: BLE001
            report.add(fail(L, "runs", f"la vista MIP lanzó {type(exc).__name__}: {exc} en {where}"))
            return report
        report.extend(_names(dom, struct, fams, obj, groups, where, granularity=not scale_instances))
        if not report.passed:
            return report
        sols = [parts.trivial_solution(inst)] + [parts.random_solution(inst, Random(s)) for s in range(n_random)]
        sols += [parts.from_answer(inst, sc["answer"]) for sc in case.solutions]
        for sol in sols:
            try:
                x = parts.to_assignment(inst, sol)
                back = parts.from_assignment(inst, x)
                aux = parts.aux_values(inst, sol)
            except Exception as exc:  # noqa: BLE001
                report.add(fail(L, "bridge_runs", f"to_assignment/from_assignment/aux_values lanzó {type(exc).__name__}: {exc} con sol={_short(sol)}"))
                return report
            # la ida y vuelta se exige a las factibles: una infactible puede no ser representable en
            # la vista MIP (un cliente repetido no tiene arcos propios)
            if decoder and not _viol(parts, inst, sol):
                # varias codificaciones dan la misma solución: se exige que la vuelta sea factible y no peor
                c_sol, c_back = sum(parts.cost_terms(inst, sol).values()), sum(parts.cost_terms(inst, back).values())
                if _viol(parts, inst, back) or (c_back > c_sol and not _close(c_back, c_sol)):
                    report.add(fail(L, "assignment_round_trip",
                                    f"from_assignment(to_assignment(sol)) debe ser factible y no peor que sol: sol={_short(sol)} "
                                    f"(costo {c_sol:.6g}), vuelta={_short(back)} (costo {c_back:.6g}, viola {_viol(parts, inst, back)})"))
                    return report
            elif back != sol and not _viol(parts, inst, sol):
                report.add(fail(L, "assignment_round_trip", f"from_assignment(to_assignment(sol)) != sol: sol={_short(sol)}, vuelta={_short(back)}"))
                return report
            if set(x) != set(struct) or set(aux) != set(dom) - set(struct):
                report.add(fail(L, "point_covers_variables",
                                f"to_assignment ∪ aux_values debe dar valor a todas las variables: faltan "
                                f"{sorted(set(dom) - set(x) - set(aux))[:5]}, sobran {sorted((set(x) | set(aux)) - set(dom))[:5]}"))
                return report
            # una solución infactible que la vista MIP no puede expresar (dos rutas idénticas se funden en
            # los mismos arcos; la vuelta es factible) no dice nada sobre las familias del MIP
            try:
                if _viol(parts, inst, sol) and not _viol(parts, inst, back):
                    continue
                report.extend(_point(parts, inst, sol, {**x, **aux}, dom, fams, obj))
            except Exception as exc:  # noqa: BLE001
                report.add(fail(L, "runs", f"violations/cost_terms lanzó {type(exc).__name__}: {exc} con sol={_short(sol)}"))
            if not report.passed:
                return report
    if report.passed:
        report.add(ok(L, "views_agree_pointwise", "familias y términos coinciden en todas las soluciones de prueba"))
    return report


def _groups(struct, groups, where, granularity: bool) -> list[CheckResult]:
    L = "semantic_mip"
    out = []
    grouped = [v for vs in groups.values() for v in vs]
    if sorted(grouped) != sorted(struct):
        out.append(fail(L, "groups_partition_structural",
                        f"variable_groups debe ser una partición de structural_variables ({where}): "
                        f"faltan {sorted(set(struct) - set(grouped))[:5]}, repetidas o ajenas {sorted({v for v in grouped if grouped.count(v) > 1 or v not in struct})[:5]}"))
    # una partición en pocos grupos es válida pero inútil: Fix-and-Optimize libera bloques de 1 a 4
    # grupos (2 por defecto), así que con 1 o 2 grupos un bloque es el MIP entero (corrida 21: un
    # grupo con los 420 arcos; corrida 22: la lista partida en 2 mitades; FIX_OPT no mejoraba nada)
    biggest = max((len(vs) for vs in groups.values()), default=0)
    if granularity and len(struct) >= 12 and (len(groups) < MIN_GROUPS or biggest > MAX_GROUP_SHARE * len(struct)):
        out.append(fail(L, "groups_split_the_problem",
                        f"variable_groups debe dividir el problema en bloques chicos ({where}): hay {len(groups)} grupo(s) y el "
                        f"mayor tiene {biggest} de {len(struct)} variables; se piden al menos {MIN_GROUPS} grupos y ninguno con "
                        f"más de un tercio. Fix-and-Optimize libera de a 1 a 4 grupos por subproblema, y con pocos grupos cada "
                        f"subproblema es casi el MIP completo. Agrupa por estructura del problema (sector, período, ítem…)."))
    return out


def _names(dom, struct, fams, obj, groups, where, granularity: bool = True) -> list[CheckResult]:
    L = "semantic_mip"
    out = []
    bad_struct = [v for v in struct if v not in dom or dom[v][2] != "binary"]
    if bad_struct:
        out.append(fail(L, "structural_are_binary", f"structural_variables debe ser un subconjunto binario de variables(): {bad_struct[:5]}"))
    out += _groups(struct, groups, where, granularity)
    used = {v for cons in fams.values() for coefs, _, _ in cons for v in coefs} | {v for coefs, _ in obj.values() for v in coefs}
    undeclared = sorted(used - set(dom))
    if undeclared:
        out.append(fail(L, "declared_variables", f"restricciones u objetivo usan variables no declaradas: {undeclared[:5]}"))
    return out or [ok(L, "names_consistent")]


def _point(parts, inst, sol, point, dom, fams, obj) -> list[CheckResult]:
    L = "semantic_mip"
    heur = {family_of(k) for k in _viol(parts, inst, sol)}
    mip: dict[str, tuple] = {}
    for fam, cons in fams.items():
        for k, c in enumerate(cons):
            amount = violated(c, point)
            if amount > 0:
                mip.setdefault(family_of(fam), (fam, k, c, amount))
                break
    inf = float("inf")
    bounds = [(v, point[v], lo, hi) for v, (lo, hi, _) in ((v, (-inf if lo is None else lo, inf if hi is None else hi, k))
                                                            for v, (lo, hi, k) in dom.items())
              if point[v] < lo - TOL * max(1, abs(lo)) or point[v] > hi + TOL * max(1, abs(hi))]
    tag = f"sol={_short(sol)}"
    if not heur:
        if mip:
            fam, k, (coefs, sense, rhs), amount = next(iter(mip.values()))
            return [fail(L, "families_agree",
                         f"la familia '{fam}' del MIP rechaza una solución que violations considera factible: restricción {k} "
                         f"({_expr(coefs)} {sense} {rhs:g}) vale {lhs(coefs, point):g} en el punto de {tag}")]
        if bounds:
            v, val, lo, hi = bounds[0]
            return [fail(L, "bounds_agree", f"la variable '{v}' vale {val:g} fuera de [{lo:g}, {hi:g}] en el punto de una solución "
                                            f"factible ({tag}); revisa aux_values o el dominio")]
        costs = parts.cost_terms(inst, sol)
        if set(costs) != set(obj):
            return [fail(L, "objective_terms_named", f"cost_terms tiene {sorted(costs)} y objective_terms {sorted(obj)}: deben ser los mismos términos")]
        for t, (coefs, const) in obj.items():
            val = lhs(coefs, point) + const
            if not _close(val, costs[t]):
                return [fail(L, "objective_terms_agree", f"el término '{t}' vale {val:.6g} en el MIP y {costs[t]:.6g} en cost_terms para {tag}")]
        return []
    if not mip and not bounds:
        # corrida 28: variables de faltante en el balance, sin costo: el MIP permitía el faltante gratis
        in_obj = {v for coefs, _ in obj.values() for v in coefs}
        struct = set(parts.structural_variables(inst))
        absorb = sorted(((v, val) for v, val in point.items() if v not in struct and v not in in_obj and abs(val) > 1e-6),
                        key=lambda kv: -abs(kv[1]))
        hint = ""
        if absorb:
            hint = (" Variables auxiliares que no están en el objetivo y valen distinto de 0 en ese punto: "
                    + ", ".join(f"{v} = {val:g}" for v, val in absorb[:5])
                    + ". Si alguna representa la violación (faltante, exceso…), el MIP la está permitiendo gratis: en el MIP "
                      "la solución tiene que ser factible, así que esa variable sobra o debe valer 0.")
        return [fail(L, "families_agree", f"violations reporta {sorted(heur)} pero el punto cumple todas las restricciones del MIP ({tag}): "
                                          f"al MIP le falta una restricción de esa familia.{hint}")]
    # Con una solución infactible no se exige que el MIP no viole otras familias: una violación
    # puede aparecer también bajo otro nombre (un cliente repetido rompe además las MTZ, que
    # también eliminan ciclos). Sí, que cada familia que reporta violations esté violada en el MIP.
    missing = sorted(heur - set(mip))
    if missing and not bounds:
        return [fail(L, "families_agree", f"violations reporta la familia {missing} pero ninguna restricción del MIP con ese nombre "
                                          f"está violada en el punto de {tag}")]
    return []


def _expr(coefs: dict[str, float], n: int = 6) -> str:
    items = list(coefs.items())
    text = " + ".join(f"{c:g}·{v}" for v, c in items[:n])
    return text + (" + …" if len(items) > n else "")


def check_mip_optimum(parts, cases: list[TestCase], time_limit: float = 20.0) -> ValidationReport:
    report = ValidationReport(subject="óptimo del MIP")
    L = "semantic_mip"
    for case in cases:
        inst, where = case.instance, _where(case)
        try:
            model = LinearMIP(parts, inst)
            x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=time_limit)
        except Exception as exc:  # noqa: BLE001
            report.add(fail(L, "full_mip_runs", f"armar o resolver el MIP completo lanzó {type(exc).__name__}: {exc} en {where}"))
            continue
        if x is None:
            report.add(fail(L, "full_mip_solvable", f"el MIP completo no encontró solución en {time_limit:g} s en {where}"))
            continue
        sol = parts.from_assignment(inst, x)
        cost = sum(parts.cost_terms(inst, sol).values())
        if _viol(parts, inst, sol):
            plan = f" (solución {_short(sol, 160)})" if case.visible else ""
            report.add(fail(L, "mip_solution_feasible",
                            f"la solución del MIP completo viola {_viol(parts, inst, sol)} según violations en {where}{plan}: el MIP "
                            f"encuentra valores de sus variables que cumplen todas sus restricciones con esa solución, y la vista "
                            f"heurística dice que no se puede. Al MIP le falta (o tiene demasiado laxa) una restricción que la "
                            f"vista heurística sí impone; revisa cada regla del enunciado contra constraint_families."))
        elif case.optimum is not None and not _close(cost, case.optimum, 1e-4):
            report.add(fail(L, "optimum_matches_cases",
                            f"el óptimo del MIP cuesta {cost:.6g} y el esperado es {case.optimum:.6g} en {where}: "
                            f"{'el MIP permite soluciones que el problema no permite' if cost < case.optimum else 'el MIP excluye soluciones válidas'}"))
        else:
            triv = sum(parts.cost_terms(inst, parts.trivial_solution(inst)).values())
            if cost > triv + 1e-6 * max(1.0, abs(triv)):
                report.add(fail(L, "full_mip_not_worse_than_trivial", f"el óptimo del MIP ({cost:.6g}) es peor que la trivial ({triv:.6g}) en {where}"))
    if report.passed:
        report.add(ok(L, "optimum_matches_cases", f"{sum(1 for c in cases if c.optimum is not None)} óptimos esperados"))
    return report


def _fingerprint(obj) -> str:
    """Huella de un parcial para detectar que apply_action lo modificó en su lugar."""
    text = repr(obj)
    if " object at 0x" not in text:
        return text
    slots = getattr(type(obj), "__slots__", ())
    state = {k: getattr(obj, k, None) for k in slots} if slots else getattr(obj, "__dict__", {})
    return repr(sorted((k, repr(v)) for k, v in state.items()))


def check_construction_view(parts, cases: list[TestCase], scale_instances: list | None = None, n_random: int = 4,
                            max_seconds: float = 10.0, max_steps: int = 20_000) -> ValidationReport:
    """La vista constructiva: completar una parcial eligiendo candidatos AL AZAR tiene que terminar y
    dar siempre una solución canónica y factible según `violations` (en los casos y en las
    instancias de tamaño realista), sin modificar las parciales, y en tiempo razonable."""
    import time

    report = ValidationReport(subject="vista constructiva")
    report.extend(_missing(parts, CONSTRUCTION_PARTS))
    if not report.passed:
        return report
    L = "construction"
    targets = [(c.instance, _where(c), c.visible) for c in cases]
    targets += [(inst, f"instancia de tamaño realista {k}", False) for k, inst in enumerate(scale_instances or [])]
    for inst, where, visible in targets:
        sols = set()
        for s in range(n_random):
            rng, trail = Random(s), []
            t0 = time.perf_counter()
            try:
                partial = parts.empty_partial(inst)
                for _step in range(max_steps):
                    if parts.is_complete(inst, partial):
                        sol, how = parts.to_solution(inst, partial), "to_solution"
                        break
                    cands = list(parts.candidates(inst, partial))
                    if not cands:
                        sol, how = parts.complete_partial(inst, partial, rng), "complete_partial (sin candidatos)"
                        break
                    action = cands[rng.randrange(len(cands))]
                    before = _fingerprint(partial)
                    nxt = parts.apply_action(inst, partial, action)
                    if _fingerprint(partial) != before:
                        report.add(fail(L, "apply_is_pure", f"apply_action modificó la parcial en su lugar en {where}: debe "
                                                            f"devolver una parcial nueva (las heurísticas comparan alternativas)"))
                        return report
                    trail.append(action)
                    partial = nxt
                    if time.perf_counter() - t0 > max_seconds:
                        report.add(fail(L, "construction_fast", f"una construcción no terminó en {max_seconds:g} s en {where} "
                                                               f"({len(trail)} pasos): candidates o apply_action son demasiado caros"))
                        return report
                else:
                    report.add(fail(L, "construction_terminates", f"la construcción no terminó en {max_steps} pasos en {where}: "
                                                                   f"is_complete nunca da True (¿apply_action no avanza?)"))
                    return report
                hash(sol)
                if parts.canonical(sol) != sol:
                    report.add(fail(L, "solution_canonical", f"{how} no devuelve la forma canónica en {where}: {_short(sol)}"))
                    return report
                v = _viol(parts, inst, sol)
            except Exception as exc:  # noqa: BLE001
                report.add(fail(L, "runs", f"la vista constructiva lanzó {type(exc).__name__}: {exc} en {where}"
                                           + (f" tras las acciones {_short(trail, 200)}" if visible else "")))
                return report
            if v:
                report.add(fail(L, "random_completion_feasible",
                                f"completar eligiendo candidatos al azar dio una solución que viola {v} en {where} (por "
                                f"{how}, {len(trail)} pasos"
                                + (f"; acciones {_short(trail, 200)}; solución {_short(sol, 160)}" if visible else "")
                                + "): candidates debe ofrecer solo acciones que se puedan completar a una solución factible, y "
                                  "complete_partial debe terminar en una factible"))
                return report
            sols.add(repr(sol))
        if len(sols) < 2 and n_random > 1 and "realista" in where:
            report.add(fail(L, "choices_matter", f"las {n_random} construcciones al azar dieron la misma solución en {where}: "
                                                 f"los candidatos no ofrecen decisiones reales, un puntaje no tendría qué elegir"))
    if report.passed:
        report.add(ok(L, "random_completions_feasible", f"{n_random} construcciones al azar por instancia, todas factibles"))
    return report


def validate_parts(parts, cases: list[TestCase], mip_time_limit: float = 20.0, scale_instances: list | None = None,
                   decoder: bool = False) -> ValidationReport:
    """Las tres etapas en orden; se detiene en la primera que falla."""
    report = ValidationReport(subject="ProblemModel por piezas")
    for step in (lambda: check_heuristic_view(parts, cases, decoder=decoder),
                 lambda: check_mip_view(parts, cases, scale_instances=scale_instances, decoder=decoder),
                 lambda: check_mip_optimum(parts, cases, mip_time_limit)):
        r = step()
        report.extend(r.results)
        if not r.passed:
            break
    return report


__all__ = ["check_construction_view", "check_heuristic_view", "check_mip_optimum", "check_mip_view", "validate_parts"]
