"""Capa 2 — contractual (§7): las propiedades verificables de la tabla de
slots (§4), ejercitadas sobre micro-instancias y con varias semillas.

Es una versión ligera de *property-based testing*: en vez de `hypothesis`
se muestrean soluciones (las triviales del contexto + las que produce
el constructor de referencia) y movimientos, con semillas fijas para
que un fallo sea reproducible y el mensaje devuelto al LLM sea concreto
("undo(apply(sol, m)) != sol para m=(3, True) en la instancia 1").
"""

from __future__ import annotations

import math
from random import Random
from typing import Any

from core.skeleton import SearchState

from .base import CheckResult, ValidationContext, fail, guard, ok

LAYER = "contractual"


def _close(a: float, b: float, tol: float) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol * 100)


def _sample_solutions(ctx: ValidationContext, inst_idx: int, constructor=None) -> list[Any]:
    sols = [ctx.trivial_solutions[inst_idx]]
    if constructor is not None:
        for seed in ctx.seeds:
            sols.append(constructor.build(ctx.instances[inst_idx], Random(seed)))
    elif ctx.baseline_constructor is not None:
        for seed in ctx.seeds:
            sols.append(ctx.baseline_constructor.build(ctx.instances[inst_idx], Random(seed)))
    return sols


# --------------------------------------------------------------------------- slots


def check_constructor(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        for seed in ctx.seeds:
            def _feasible(k=k, inst=inst, seed=seed):
                sol = impl.build(inst, Random(seed))
                if not ctx.problem.is_feasible(sol):
                    return fail(LAYER, "constructor.feasible", f"build(inst_{k}, seed={seed}) produjo una solución infactible")
                return ok(LAYER, "constructor.feasible")

            def _deterministic(k=k, inst=inst, seed=seed):
                a = impl.build(inst, Random(seed))
                b = impl.build(inst, Random(seed))
                if a != b:
                    return fail(LAYER, "constructor.deterministic", f"dos llamadas con seed={seed} en inst_{k} difieren")
                return ok(LAYER, "constructor.deterministic")

            results += guard(LAYER, "constructor.feasible", _feasible)
            results += guard(LAYER, "constructor.deterministic", _deterministic)
    return _collapse(results)


def check_neighborhood(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    f = ctx.problem.objective
    for k in range(len(ctx.instances)):
        for sol in _sample_solutions(ctx, k):
            def _props(k=k, sol=sol):
                out = []
                moves = list(impl.moves(sol))
                if not moves:
                    return [fail(LAYER, "neighborhood.nonempty", f"moves(sol) vacío en inst_{k}")]
                rng = Random(0)
                sample = moves if len(moves) <= ctx.max_moves_checked else rng.sample(moves, ctx.max_moves_checked)
                f_sol = f(sol)
                for m in sample:
                    applied = impl.apply(sol, m)
                    if impl.undo(applied, m) != sol:
                        out.append(fail(LAYER, "neighborhood.undo_apply_identity", f"undo(apply(sol, m)) != sol para m={m!r} en inst_{k}"))
                        break
                    d = impl.delta(sol, m)
                    if not _close(d, f(applied) - f_sol, ctx.tolerance):
                        out.append(fail(LAYER, "neighborhood.delta_consistent", f"delta={d:.6g} pero f(apply)-f(sol)={f(applied) - f_sol:.6g} para m={m!r} en inst_{k}"))
                        break
                    if ctx.require_feasible_moves and not ctx.problem.is_feasible(applied):
                        out.append(fail(LAYER, "neighborhood.feasible_after_apply", f"apply(sol, m={m!r}) infactible en inst_{k}"))
                        break
                return out or [ok(LAYER, "neighborhood.undo_apply_identity"), ok(LAYER, "neighborhood.delta_consistent")]

            results += guard(LAYER, "neighborhood", _props)
    return _collapse(results)


def check_evaluator(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for k in range(len(ctx.instances)):
        for sol in _sample_solutions(ctx, k):
            def _full(k=k, sol=sol):
                if not _close(impl.full(sol), ctx.problem.objective(sol), ctx.tolerance):
                    return fail(LAYER, "evaluator.full_matches_objective", f"full(sol)={impl.full(sol):.6g} != objective(sol)={ctx.problem.objective(sol):.6g} en inst_{k}")
                return ok(LAYER, "evaluator.full_matches_objective")

            results += guard(LAYER, "evaluator.full_matches_objective", _full)
            if ctx.reference_neighborhood is not None:
                def _incr(k=k, sol=sol):
                    nbh = ctx.reference_neighborhood
                    for m in list(nbh.moves(sol))[: ctx.max_moves_checked]:
                        inc, full = impl.incremental(sol, m), impl.full(nbh.apply(sol, m))
                        if not _close(inc, full, ctx.tolerance):
                            return fail(LAYER, "evaluator.incremental_consistent", f"incremental={inc:.6g} vs full(apply)={full:.6g} para m={m!r} en inst_{k}")
                    return ok(LAYER, "evaluator.incremental_consistent")

                results += guard(LAYER, "evaluator.incremental_consistent", _incr)
    return _collapse(results)


def check_acceptance(impl, ctx: ValidationContext) -> list[CheckResult]:
    def _monotone():
        state = SearchState(extra={"temperature": 1.0, "rng": Random(0)})
        for f_cur in (0.0, 10.0, -5.0, 1e6):
            if not impl.accept(f_cur, f_cur - 1.0, state):
                return fail(LAYER, "acceptance.accepts_improvement", f"accept(f_cur={f_cur}, f_cand={f_cur - 1.0}) devolvió False")
        return ok(LAYER, "acceptance.accepts_improvement")

    def _returns_bool():
        state = SearchState(extra={"temperature": 1.0, "rng": Random(0)})
        r = impl.accept(1.0, 2.0, state)
        if not isinstance(r, bool):
            return fail(LAYER, "acceptance.returns_bool", f"accept devolvió {type(r).__name__}, no bool")
        return ok(LAYER, "acceptance.returns_bool")

    return guard(LAYER, "acceptance.accepts_improvement", _monotone) + guard(LAYER, "acceptance.returns_bool", _returns_bool)


def check_perturbation(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for k in range(len(ctx.instances)):
        sol = ctx.trivial_solutions[k]

        def _changes(k=k, sol=sol):
            changed = sum(impl.perturb(sol, 1.0, Random(s)) != sol for s in ctx.seeds)
            if changed == 0:
                return fail(LAYER, "perturbation.changes_solution", f"perturb(sol, strength=1) devolvió la misma solución con todas las semillas en inst_{k}")
            return ok(LAYER, "perturbation.changes_solution")

        def _feasible(k=k, sol=sol):
            if ctx.require_feasible_moves:
                for s in ctx.seeds:
                    if not ctx.problem.is_feasible(impl.perturb(sol, 1.0, Random(s))):
                        return fail(LAYER, "perturbation.feasible", f"perturb produjo infactible (seed={s}) en inst_{k}")
            return ok(LAYER, "perturbation.feasible")

        results += guard(LAYER, "perturbation.changes_solution", _changes)
        results += guard(LAYER, "perturbation.feasible", _feasible)
    return _collapse(results)


def check_destruction(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        all_vars = ctx.variables(inst)
        sol = ctx.trivial_solutions[k]
        for ratio in (0.1, 0.5):
            def _props(k=k, sol=sol, ratio=ratio, all_vars=all_vars):
                partial, free = impl.destroy(sol, ratio, Random(0))
                free = set(free)
                if not free:
                    return fail(LAYER, "destruction.frees_something", f"destroy(ratio={ratio}) no liberó variables en inst_{k}")
                if not free <= all_vars:
                    return fail(LAYER, "destruction.free_subset_of_variables", f"free_vars contiene {sorted(free - all_vars)[:5]} que no son variables de inst_{k}")
                if isinstance(partial, dict):
                    keys = set(partial)
                    if keys & free:
                        return fail(LAYER, "destruction.partial_consistent", f"parcial contiene variables liberadas: {sorted(keys & free)[:5]}")
                    if keys | free != all_vars:
                        return fail(LAYER, "destruction.partial_consistent", f"parcial ∪ free no cubre todas las variables (faltan {sorted(all_vars - keys - free)[:5]})")
                    assignment = ctx.problem.to_assignment(sol)
                    wrong = [v for v in keys if not _close(partial[v], assignment[v], ctx.tolerance)]
                    if wrong:
                        return fail(LAYER, "destruction.partial_consistent", f"parcial cambia el valor de variables no liberadas: {wrong[:5]}")
                return ok(LAYER, "destruction.free_subset_of_variables")

            results += guard(LAYER, "destruction", _props)
    return _collapse(results)


def check_repair_mip(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        sol = ctx.trivial_solutions[k]
        model = ctx.problem.build_mip(inst)
        all_vars = ctx.variables(inst)
        assignment = ctx.problem.to_assignment(sol)

        def _props(k=k, sol=sol, model=model, all_vars=all_vars, assignment=assignment):
            if ctx.reference_destruction is not None:
                _p, free = ctx.reference_destruction.destroy(sol, 0.3, Random(0))
            else:
                names = sorted(all_vars)
                free = set(Random(0).sample(names, max(1, len(names) // 3)))
            fixed = {v: val for v, val in assignment.items() if v not in free}
            cand = impl.repair_mip(model, fixed, set(free), ctx.mip_time_limit, warm_start=assignment)
            if cand is None:
                return fail(LAYER, "repair_mip.returns_solution", f"repair_mip devolvió None con `sol` factible fijada en inst_{k} (el sub-MIP debería ser factible)")
            if not ctx.problem.is_feasible(cand):
                return fail(LAYER, "repair_mip.feasible", f"repair_mip devolvió una solución infactible en inst_{k}")
            cand_assign = ctx.problem.to_assignment(cand)
            moved = [v for v in fixed if not _close(cand_assign[v], fixed[v], ctx.tolerance)]
            if moved:
                return fail(LAYER, "repair_mip.respects_fixed", f"repair_mip cambió variables fijadas: {moved[:5]} en inst_{k}")
            f_sol, f_cand = ctx.problem.objective(sol), ctx.problem.objective(cand)
            if f_cand > f_sol + ctx.tolerance * max(1.0, abs(f_sol)):
                return fail(LAYER, "repair_mip.not_worse_than_incumbent", f"f(cand)={f_cand:.6g} > f(sol)={f_sol:.6g} en inst_{k}: con `sol` factible en el sub-MIP y warm start, un sub-MIP correcto no empeora")
            return ok(LAYER, "repair_mip.not_worse_than_incumbent")

        results += guard(LAYER, "repair_mip", _props)
    return _collapse(results)


def check_fixing_policy(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        groups = ctx.problem.variable_groups(inst)
        all_vars = ctx.variables(inst)

        def _schedule(k=k, groups=groups, all_vars=all_vars):
            covered: set[str] = set()
            for step, (fix, integer, relax) in enumerate(impl.schedule(groups, None)):
                fix, integer, relax = set(fix), set(integer), set(relax)
                if fix | integer | relax != all_vars or (fix & integer) or (fix & relax) or (integer & relax):
                    return fail(LAYER, "fixing_policy.partition", f"paso {step} en inst_{k}: (fix, int, relax) no es partición de las variables")
                if not integer:
                    return fail(LAYER, "fixing_policy.partition", f"paso {step} en inst_{k}: integer_set vacío")
                covered |= integer
            if covered != all_vars:
                return fail(LAYER, "fixing_policy.covers_all", f"la agenda nunca hace enteras a {sorted(all_vars - covered)[:5]} en inst_{k}")
            return ok(LAYER, "fixing_policy.covers_all")

        def _blocks(k=k, groups=groups, all_vars=all_vars):
            blocks = [set(b) for b in impl.blocks(groups, 2)]
            union = set().union(*blocks) if blocks else set()
            if union != all_vars:
                return fail(LAYER, "fixing_policy.blocks_cover_all", f"blocks() no cubre todas las variables en inst_{k}")
            return ok(LAYER, "fixing_policy.blocks_cover_all")

        results += guard(LAYER, "fixing_policy.schedule", _schedule)
        results += guard(LAYER, "fixing_policy.blocks", _blocks)
    return _collapse(results)


def check_stop(impl, ctx: ValidationContext) -> list[CheckResult]:
    def _eventually():
        state = SearchState(iteration=10**9, elapsed_time=1e9, iters_without_improvement=10**9)
        if not impl.stop(state):
            return fail(LAYER, "stop.eventually_true", "stop(state) sigue siendo False con iteration=1e9, elapsed_time=1e9, iters_without_improvement=1e9")
        return ok(LAYER, "stop.eventually_true")

    def _not_immediately():
        state = SearchState()
        if impl.stop(state):
            return fail(LAYER, "stop.not_immediately_true", "stop(state) es True en el estado inicial: el esqueleto no haría ninguna iteración")
        return ok(LAYER, "stop.not_immediately_true")

    return guard(LAYER, "stop.eventually_true", _eventually) + guard(LAYER, "stop.not_immediately_true", _not_immediately)


CHECKERS = {
    "constructor": check_constructor,
    "neighborhood": check_neighborhood,
    "evaluator": check_evaluator,
    "acceptance": check_acceptance,
    "perturbation": check_perturbation,
    "destruction": check_destruction,
    "repair_mip": check_repair_mip,
    "fixing_policy": check_fixing_policy,
    "stop": check_stop,
}


def check_slot(slot: str, impl, ctx: ValidationContext) -> list[CheckResult]:
    checker = CHECKERS.get(slot)
    if checker is None:
        return [ok(LAYER, "no_checker", f"sin propiedades contractuales definidas para el slot '{slot}'")]
    return checker(impl, ctx)


def _collapse(results: list[CheckResult]) -> list[CheckResult]:
    """Un resultado por nombre de check: FAIL si alguno falló (con su mensaje), OK si todos pasaron."""
    by_name: dict[str, CheckResult] = {}
    for r in results:
        if r.name not in by_name or (not r.passed and by_name[r.name].passed):
            by_name[r.name] = r
    return list(by_name.values())
