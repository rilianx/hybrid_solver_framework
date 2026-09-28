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

from .base import CheckResult, ValidationContext, fail, guard, ok, describe_exception

LAYER = "contractual"


def _close(a: float, b: float, tol: float) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol * 100)


def _why_infeasible(ctx: ValidationContext, sol) -> str:
    """Detalle de infactibilidad si el ProblemModel sabe darlo (opcional en el Protocol)."""
    explain = getattr(ctx.problem, "explain_infeasibility", None)
    if explain is None:
        return ""
    try:
        return " Detalle: " + explain(sol)
    except Exception:  # noqa: BLE001
        return ""


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
                    return fail(LAYER, "constructor.feasible", f"build(inst_{k}, seed={seed}) produjo una solución infactible.{_why_infeasible(ctx, sol)}")
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


def _short(obj, n: int = 300) -> str:
    text = repr(obj)
    return text if len(text) <= n else text[:n] + "…"


def check_neighborhood(impl, ctx: ValidationContext) -> list[CheckResult]:
    results: list[CheckResult] = []
    has_undo = callable(getattr(impl, "undo", None))
    f = ctx.problem.objective
    empty: list[int] = []
    for k in range(len(ctx.instances)):
        sols = _sample_solutions(ctx, k)
        empty.clear()
        for sol in sols:
            def _props(k=k, sol=sol):
                out = []
                moves = list(impl.moves(sol))
                if not moves:
                    empty.append(k)  # puede ser legítimo en una solución concreta (2-opt sobre rutas de un cliente)
                    return []
                rng = Random(0)
                sample = moves if len(moves) <= ctx.max_moves_checked else rng.sample(moves, ctx.max_moves_checked)
                f_sol = f(sol)
                for m in sample:
                    step = "apply"
                    try:
                        applied = impl.apply(sol, m)
                        step = "undo"
                        back = impl.undo(applied, m) if has_undo else sol  # opcional: ver core.contracts.Neighborhood
                        step = "delta"
                        d = impl.delta(sol, m)
                    except Exception as exc:  # noqa: BLE001 — con el movimiento y la solución, el LLM puede corregirlo
                        out.append(fail(LAYER, f"neighborhood.{step}_runs",
                                        f"{step}(…, m={m!r}) lanzó {describe_exception(exc)}. m salió de moves(sol) con "
                                        f"sol={_short(sol)} en inst_{k}"))
                        break
                    if back != sol:
                        out.append(fail(LAYER, "neighborhood.undo_apply_identity",
                                        f"undo(apply(sol, m)) != sol para m={m!r} en inst_{k}: sol={_short(sol)}, "
                                        f"apply(sol, m)={_short(applied)}, undo(...)={_short(back)}"))
                        break
                    if not _close(d, f(applied) - f_sol, ctx.tolerance):
                        out.append(fail(LAYER, "neighborhood.delta_consistent", f"delta={d:.6g} pero f(apply)-f(sol)={f(applied) - f_sol:.6g} para m={m!r} en inst_{k}"))
                        break
                    if ctx.require_feasible_moves and not ctx.problem.is_feasible(applied):
                        out.append(fail(LAYER, "neighborhood.feasible_after_apply", f"apply(sol, m={m!r}) infactible en inst_{k}"))
                        break
                return out or [ok(LAYER, "neighborhood.undo_apply_identity"), ok(LAYER, "neighborhood.delta_consistent")]

            results += guard(LAYER, "neighborhood", _props)
            if callable(getattr(impl, "sample", None)):
                results += guard(LAYER, "neighborhood.sample", lambda k=k, sol=sol: _check_sample(impl, sol, k))
        # vacío en UNA solución puede ser correcto (CVRP: 2-opt u or-opt sobre rutas de un cliente);
        # vacío en todas las de prueba de la instancia, no
        if len(empty) == len(sols):
            results.append(fail(LAYER, "neighborhood.nonempty", f"moves(sol) vacío en todas las soluciones de prueba de inst_{k}"))
    return _collapse(results)


def _check_sample(impl, sol, k: int) -> CheckResult:
    """`sample(sol, n, rng)` opcional (`core.neighborhood.SampledNeighborhood`): hasta n
    movimientos distintos de `moves(sol)`, deterministas dada la semilla."""
    moves = list(impl.moves(sol))
    try:
        universe = set(moves)
    except TypeError:
        universe = None
    for n in (1, 5):
        got = list(impl.sample(sol, n, Random(3)))
        if len(got) > n:
            return fail(LAYER, "neighborhood.sample", f"sample(sol, {n}, rng) devolvió {len(got)} movimientos en inst_{k}")
        if len(got) < min(n, len(moves)):
            return fail(LAYER, "neighborhood.sample", f"sample(sol, {n}, rng) devolvió {len(got)} movimientos y moves(sol) tiene {len(moves)} en inst_{k}")
        if got != list(impl.sample(sol, n, Random(3))):
            return fail(LAYER, "neighborhood.sample", f"dos llamadas a sample(sol, {n}, rng) con la misma semilla difieren en inst_{k}")
        if universe is not None:
            if len(set(got)) != len(got):
                return fail(LAYER, "neighborhood.sample", f"sample(sol, {n}, rng) repite movimientos en inst_{k}")
            extra = [m for m in got if m not in universe]
            if extra:
                return fail(LAYER, "neighborhood.sample", f"sample devolvió {extra[0]!r}, que no está en moves(sol) (inst_{k})")
    return ok(LAYER, "neighborhood.sample")


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

        def _changes(k=k):
            # sin cambios en UNA solución puede ser correcto (intercambiar clientes entre rutas de un
            # cliente no cambia nada); sin cambios en todas las de prueba, no
            sols = _sample_solutions(ctx, k)
            changed = sum(impl.perturb(x, 1.0, Random(s)) != x for x in sols for s in ctx.seeds)
            if changed == 0:
                return fail(LAYER, "perturbation.changes_solution",
                            f"perturb(sol, strength=1) devolvió la misma solución con todas las semillas y todas las soluciones de prueba en inst_{k}")
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
                return fail(LAYER, "repair_mip.feasible", f"repair_mip devolvió una solución infactible en inst_{k}.{_why_infeasible(ctx, cand)}")
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


def check_greedy_score(impl, ctx: ValidationContext) -> list[CheckResult]:
    """Slot `greedy_score`. Sobre estados parciales reales (una construcción con elección al
    azar entre los candidatos): el puntaje es finito, determinista y no modifica el parcial.
    Después, el constructor greedy que arma cumple lo mismo que cualquier constructor
    (factible y determinista), con la regla greedy y con la RCL."""
    import pickle

    from core.construction import GreedyConstructor

    if not callable(getattr(ctx.problem, "construction_view", None)):
        return [fail(LAYER, "greedy_score.view", "el ProblemModel no expone `construction_view(inst)`: no hay dónde usar un puntaje")]
    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        def _props(k=k, inst=inst):
            view = ctx.problem.construction_view(inst)
            partial, rng = view.empty(), Random(k)
            for _ in range(60):
                if view.is_complete(partial):
                    break
                cands = list(view.candidates(partial))
                if not cands:
                    break
                for c in cands[:15]:
                    before = pickle.dumps(partial)
                    a, b = impl.score(partial, c), impl.score(partial, c)
                    if not isinstance(a, (int, float)) or math.isnan(a) or math.isinf(a):
                        return fail(LAYER, "greedy_score.finite", f"score devolvió {a!r} para la acción {c!r} en inst_{k}: debe ser un número finito")
                    if a != b:
                        return fail(LAYER, "greedy_score.deterministic", f"dos llamadas a score con el mismo parcial y la acción {c!r} dan {a} y {b} (inst_{k})")
                    if pickle.dumps(partial) != before:
                        return fail(LAYER, "greedy_score.pure", f"score modificó el estado parcial al puntuar {c!r} (inst_{k}): debe solo leerlo")
                partial = view.apply(partial, cands[rng.randrange(len(cands))])
            return ok(LAYER, "greedy_score.finite")

        results += guard(LAYER, "greedy_score.finite", _props)
    if any(not r.passed for r in results):
        return _collapse(results)
    for rule in ("greedy", "rcl"):
        for r in check_constructor(GreedyConstructor(ctx.problem, impl, rule=rule, alpha=0.3), ctx):
            results.append(CheckResult(r.layer, r.name, r.passed, (f"[constructor greedy, regla {rule}] " + r.message) if r.message else r.message))
    return _collapse(results)


def check_construction_policy(impl, ctx: ValidationContext) -> list[CheckResult]:
    """Slot `construction_policy` (puntaje con memoria). Sobre construcciones reales con
    elección al azar: `init` y `update` dan memorias hashables y deterministas, `score` es finito
    y determinista, y ninguno modifica el parcial ni la memoria que recibe. Después, el
    constructor greedy que arma cumple lo mismo que cualquier constructor, con la regla greedy y
    con la RCL: factible, determinista y termina."""
    import pickle

    from core.construction import GreedyConstructor

    L = "construction_policy"
    if not callable(getattr(ctx.problem, "construction_view", None)):
        return [fail(LAYER, f"{L}.view", "el ProblemModel no expone `construction_view(inst)`: no hay dónde usar una política")]

    def _hashable(m, what, k):
        try:
            hash(m)
        except TypeError:
            return fail(LAYER, f"{L}.memory_hashable", f"{what} devolvió una memoria no hashable ({type(m).__name__}) en inst_{k}: "
                                                      f"usa tuplas, frozensets o un dataclass(frozen=True)")
        return None

    results: list[CheckResult] = []
    for k, inst in enumerate(ctx.instances):
        def _props(k=k, inst=inst):
            view = ctx.problem.construction_view(inst)
            partial, rng = view.empty(), Random(k)
            m0, m1 = impl.init(partial), impl.init(partial)
            bad = _hashable(m0, "init", k)
            if bad:
                return bad
            if m0 != m1:
                return fail(LAYER, f"{L}.deterministic", f"dos llamadas a init con el mismo parcial dan memorias distintas (inst_{k})")
            memory = m0
            for _ in range(60):
                if view.is_complete(partial):
                    break
                cands = list(view.candidates(partial))
                if not cands:
                    break
                for c in cands[:15]:
                    before = (pickle.dumps(partial), pickle.dumps(memory))
                    a, b = impl.score(partial, memory, c), impl.score(partial, memory, c)
                    if not isinstance(a, (int, float)) or math.isnan(a) or math.isinf(a):
                        return fail(LAYER, f"{L}.finite", f"score devolvió {a!r} para la acción {c!r} en inst_{k}: debe ser un número finito")
                    if a != b:
                        return fail(LAYER, f"{L}.deterministic", f"dos llamadas a score con el mismo parcial, memoria y acción {c!r} dan {a} y {b} (inst_{k})")
                    u, v = impl.update(partial, memory, c), impl.update(partial, memory, c)
                    bad = _hashable(u, "update", k)
                    if bad:
                        return bad
                    if u != v:
                        return fail(LAYER, f"{L}.deterministic", f"dos llamadas a update con la acción {c!r} dan memorias distintas (inst_{k})")
                    if (pickle.dumps(partial), pickle.dumps(memory)) != before:
                        return fail(LAYER, f"{L}.pure", f"score o update modificó el parcial o la memoria al procesar {c!r} (inst_{k}): "
                                                        f"deben solo leerlos (update devuelve una memoria NUEVA)")
                action = cands[rng.randrange(len(cands))]
                memory = impl.update(partial, memory, action)
                partial = view.apply(partial, action)
            return ok(LAYER, f"{L}.finite")

        results += guard(LAYER, f"{L}.finite", _props)
    if any(not r.passed for r in results):
        return _collapse(results)
    for rule in ("greedy", "rcl"):
        for r in check_constructor(GreedyConstructor(ctx.problem, impl, rule=rule, alpha=0.3, max_steps=20_000), ctx):
            results.append(CheckResult(r.layer, r.name, r.passed, (f"[constructor greedy, regla {rule}] " + r.message) if r.message else r.message))
    return _collapse(results)


def check_construction_machine(impl, ctx: ValidationContext) -> list[CheckResult]:
    """Slot `construction_machine`. `states` es una tupla de nombres distintos; `initial` y
    `transition` dan (estado de `states`, memoria hashable). Corrida como política
    (`core.machine.MachinePolicy`) cumple lo mismo que una `construction_policy`: memorias
    deterministas, score finito, nada modifica el parcial ni la memoria, y el greedy que arma es
    factible, determinista y termina. Además cada estado se alcanza en alguna construcción (greedy
    o con la RCL): un estado que nunca se usa es código muerto."""
    from core.construction import GreedyConstructor
    from core.machine import MachinePolicy, machine_trace

    L = "construction_machine"
    states = getattr(impl, "states", None)
    if not (isinstance(states, tuple) and states and all(isinstance(x, str) for x in states) and len(set(states)) == len(states)):
        return [fail(LAYER, f"{L}.states", f"`states` debe ser una tupla no vacía de nombres distintos (str), no {states!r}")]
    if not callable(getattr(ctx.problem, "construction_view", None)):
        return [fail(LAYER, f"{L}.view", "el ProblemModel no expone `construction_view(inst)`: no hay dónde usar una máquina")]

    def _initial():
        view = ctx.problem.construction_view(ctx.instances[0])
        out = impl.initial(view.empty())
        if not (isinstance(out, tuple) and len(out) == 2 and out[0] in states):
            return fail(LAYER, f"{L}.initial", f"initial debe devolver (estado de {states}, memoria), no {out!r}")
        return ok(LAYER, f"{L}.initial")

    results = guard(LAYER, f"{L}.initial", _initial)
    if any(not r.passed for r in results):
        return results
    policy = MachinePolicy(impl)
    for r in check_construction_policy(policy, ctx):
        name = r.name.replace("construction_policy.", f"{L}.")
        results.append(CheckResult(r.layer, name, r.passed, r.message))
    if any(not r.passed for r in results):
        return _collapse(results)

    def _reach():
        seen: set = set()
        for k, inst in enumerate(ctx.instances):
            view = ctx.problem.construction_view(inst)
            seen |= {st for st, _ in machine_trace(policy, view, max_steps=20_000)}
            for s in range(3):  # con la RCL se recorren otros caminos
                g = GreedyConstructor(ctx.problem, policy, rule="rcl", alpha=0.5, max_steps=20_000)
                partial = view.empty()
                memory = policy.init(partial)
                rng = Random(100 + s)
                for _ in range(20_000):
                    if view.is_complete(partial):
                        break
                    cands = list(view.candidates(partial))
                    if not cands:
                        break
                    seen.add(policy.state_of(partial, memory))
                    a = g._pick(cands, g.scores(partial, cands, memory), rng)
                    memory = policy.update(partial, memory, a)
                    partial = view.apply(partial, a)
        missing = [x for x in states if x not in seen]
        if missing:
            return fail(LAYER, f"{L}.states_reachable",
                        f"los estados {missing} nunca se alcanzan en las micro-instancias (greedy y RCL): revisa las condiciones "
                        f"de transition que llevan a ellos, o quítalos")
        return ok(LAYER, f"{L}.states_reachable", f"estados alcanzados: {sorted(seen)}")

    results += guard(LAYER, f"{L}.states_reachable", _reach)
    return _collapse(results)


CHECKERS = {
    "constructor": check_constructor,
    "greedy_score": check_greedy_score,
    "construction_policy": check_construction_policy,
    "construction_machine": check_construction_machine,
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
