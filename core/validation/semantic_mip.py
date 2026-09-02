"""Capa 3 — semántica del modelo MIP (§7): cada vista valida a la otra.

Sobre micro-instancias y soluciones factibles triviales:

1. `to_assignment(sol)` fijado en el MIP completo es **factible**.
2. El objetivo del MIP con `sol` fijada coincide con `P.objective(sol)`
   (± tolerancia). Un desacuerdo revela un error en el evaluador
   heurístico *o* en la formulación — no se sabe cuál, pero se sabe que
   hay uno, que es lo que importa para rechazar y pedir corrección.
3. `from_assignment(to_assignment(sol)) == sol` (el puente es consistente).
4. El óptimo del MIP completo (si el solver lo cierra en el tiempo dado)
   no es peor que ninguna solución conocida; y si el contexto provee
   `enumerate_solutions`, coincide con el óptimo por fuerza bruta
   (micro-instancias con óptimo conocido por enumeración, §9 riesgos).
"""

from __future__ import annotations

import math
from typing import Any

from .base import CheckResult, ValidationContext, fail, guard, ok

LAYER = "semantic_mip"


def _close(a: float, b: float, tol: float) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol * 100)


def check_problem_model_mip(ctx: ValidationContext) -> list[CheckResult]:
    P = ctx.problem
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        sol = ctx.trivial_solutions[k]
        model = P.build_mip(inst)

        def _round_trip(k=k, sol=sol):
            if P.from_assignment(P.to_assignment(sol)) != sol:
                return fail(LAYER, "assignment_round_trip", f"from_assignment(to_assignment(sol)) != sol en inst_{k}")
            return ok(LAYER, "assignment_round_trip")

        def _variables_match(k=k, inst=inst, model=model):
            mip_vars, group_vars = set(model.variables()), ctx.variables(inst)
            if mip_vars != group_vars:
                return fail(LAYER, "variables_match_groups", f"variables del MIP y de variable_groups difieren en inst_{k}: solo-MIP={sorted(mip_vars - group_vars)[:5]}, solo-groups={sorted(group_vars - mip_vars)[:5]}")
            return ok(LAYER, "variables_match_groups")

        def _fixed_feasible_and_same_objective(k=k, sol=sol, model=model):
            assignment = P.to_assignment(sol)
            x = model.solve(fixed=assignment, integer=set(), relaxed=set(), time_limit=ctx.mip_time_limit)
            if x is None:
                return [fail(LAYER, "fixed_solution_feasible_in_mip", f"la solución trivial factible de inst_{k} es infactible en el MIP: la formulación es más restrictiva que la vista heurística (o la solución trivial está mal)")]
            out = [ok(LAYER, "fixed_solution_feasible_in_mip")]
            if P.from_assignment(x) != sol:
                out.append(fail(LAYER, "fixed_solution_preserved", f"fijar to_assignment(sol) y leer de vuelta no devuelve `sol` en inst_{k}"))
            mip_obj = getattr(model, "last_objective", None)
            if mip_obj is None:
                out.append(fail(LAYER, "objective_agreement", "el MIPModel no expone last_objective tras solve()"))
            elif not _close(mip_obj, P.objective(sol), max(ctx.tolerance, 1e-4)):
                out.append(fail(LAYER, "objective_agreement", f"objetivo MIP={mip_obj:.6g} vs heurístico={P.objective(sol):.6g} para la misma solución en inst_{k}: evaluador o formulación incorrectos"))
            else:
                out.append(ok(LAYER, "objective_agreement"))
            return out

        def _optimum_consistency(k=k, inst=inst, sol=sol, model=model):
            x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=ctx.mip_time_limit)
            if x is None:
                return fail(LAYER, "full_mip_solvable", f"el MIP completo de inst_{k} no devolvió solución en {ctx.mip_time_limit}s")
            f_opt = P.objective(P.from_assignment(x))
            f_sol = P.objective(sol)
            if f_opt > f_sol + max(ctx.tolerance, 1e-4) * max(1.0, abs(f_sol)):
                return fail(LAYER, "full_mip_not_worse_than_known", f"óptimo MIP={f_opt:.6g} peor que la solución trivial={f_sol:.6g} en inst_{k} (¿MIP no cerró, o formulación sobre-restringida?)")
            if ctx.enumerate_solutions is not None:
                feas = [s for s in ctx.enumerate_solutions(inst) if P.is_feasible(s)]
                brute = min(P.objective(s) for s in feas)
                if not _close(brute, f_opt, max(ctx.tolerance, 1e-4)):
                    return fail(LAYER, "full_mip_matches_brute_force", f"óptimo MIP={f_opt:.6g} vs fuerza bruta={brute:.6g} en inst_{k}")
                return ok(LAYER, "full_mip_matches_brute_force")
            return ok(LAYER, "full_mip_not_worse_than_known")

        results += guard(LAYER, "assignment_round_trip", _round_trip)
        results += guard(LAYER, "variables_match_groups", _variables_match)
        results += guard(LAYER, "fixed_solution_feasible_in_mip", _fixed_feasible_and_same_objective)
        results += guard(LAYER, "full_mip_consistency", _optimum_consistency)
    return _collapse(results)


def _collapse(results: list[CheckResult]) -> list[CheckResult]:
    by_name: dict[str, CheckResult] = {}
    for r in results:
        if r.name not in by_name or (not r.passed and by_name[r.name].passed):
            by_name[r.name] = r
    return list(by_name.values())
