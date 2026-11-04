"""ProblemModel por piezas: el ensamblador, el MIP genérico y la validación contra casos de
prueba, que tiene que LOCALIZAR el error (qué pieza, qué familia, qué término)."""

from __future__ import annotations

import types
from random import Random

import pytest

from core.model_parts import LinearMIP, PartsModel
from core.validation.model_parts import check_heuristic_view, check_mip_optimum, check_mip_view, validate_parts
from examples.cvrp import model_parts as ref
from examples.cvrp.cases import brute_force_optimum, load_cases


@pytest.fixture(scope="module")
def cases():
    return load_cases()


def mutant(**overrides):
    """Las piezas de referencia con algunas funciones reemplazadas."""
    m = types.SimpleNamespace(**{k: getattr(ref, k) for k in dir(ref) if not k.startswith("_")})
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


def test_reference_parts_pass_and_the_mip_matches_brute_force(cases):
    report = validate_parts(ref, cases)
    assert report.passed, report.feedback()
    inst = cases[0].instance
    assert brute_force_optimum(inst)[0] == pytest.approx(cases[0].optimum, abs=1e-5)


def test_assembled_model_is_a_problem_model(cases):
    inst = cases[3].instance
    P = PartsModel(ref, inst)
    triv = ref.trivial_solution(inst)
    assert P.is_feasible(triv) and P.objective(triv) == pytest.approx(ref.cost_terms(inst, triv)["distancia"])
    bad = ref.from_answer(inst, [list(inst.customers)[1:]])
    assert not P.is_feasible(bad) and P.objective(bad) > P.objective(triv)


def test_forgetting_the_return_leg_in_cost_terms_fails_against_the_cases(cases):
    def cost_terms(inst, sol):
        return {"distancia": sum(inst.dist(a, b) for r in sol for a, b in zip((0, *r), r))}

    report = check_heuristic_view(mutant(cost_terms=cost_terms), cases)
    assert not report.passed and "cost_matches_cases" in report.feedback()


def test_ignoring_capacity_in_violations_fails_with_the_expected_family(cases):
    def violations(inst, sol):
        return {"visita": ref.violations(inst, sol)["visita"]}

    report = check_heuristic_view(mutant(violations=violations), cases)
    msg = report.feedback()
    assert not report.passed and "feasibility_matches_cases" in msg and "capacidad" in msg


def test_objective_term_mismatch_is_named_by_term(cases):
    def objective_terms(inst):
        coefs, const = ref.objective_terms(inst)["distancia"]
        return {"distancia": ({v: c for v, c in coefs.items() if not v.endswith("_0")}, const)}  # sin los arcos de vuelta

    report = check_mip_view(mutant(objective_terms=objective_terms), cases)
    msg = report.feedback()
    assert not report.passed and "objective_terms_agree" in msg and "'distancia'" in msg


def test_a_wrong_constraint_is_named_by_family_on_a_feasible_point(cases):
    def constraint_families(inst):
        fams = ref.constraint_families(inst)
        fams["capacidad.mtz"] = [(coefs, "<=", rhs) for coefs, _, rhs in fams["capacidad.mtz"]]  # sentido invertido
        return fams

    report = check_mip_view(mutant(constraint_families=constraint_families), cases)
    msg = report.feedback()
    assert not report.passed and "families_agree" in msg and "capacidad.mtz" in msg and "considera factible" in msg


def test_a_missing_family_is_detected_on_an_infeasible_point(cases):
    def constraint_families(inst):
        return {k: v for k, v in ref.constraint_families(inst).items() if not k.startswith("capacidad")}

    report = check_mip_view(mutant(constraint_families=constraint_families), cases)
    msg = report.feedback()
    assert not report.passed and "capacidad" in msg
    assert "le falta una restricción" in msg or "ninguna restricción del MIP con ese nombre" in msg


def test_hidden_cases_report_expected_vs_obtained_without_the_instance(cases):
    def constraint_families(inst):  # un MIP demasiado laxo: el óptimo queda por debajo del esperado
        fams = ref.constraint_families(inst)
        fams["capacidad.carga"] = [c for c in fams["capacidad.carga"] if c[1] == ">="]
        return fams

    hidden = [c for c in cases if not c.visible]
    report = check_mip_optimum(mutant(constraint_families=constraint_families), hidden, time_limit=10)
    msg = report.feedback()
    if not report.passed:  # en algún caso oculto la capacidad aprieta
        assert "caso oculto" in msg and "el esperado es" in msg and "permite soluciones" in msg
        assert hidden[0].instance.to_text() not in msg


def test_linear_mip_supports_fixing_relaxing_and_local_branching(cases):
    inst = cases[2].instance
    model = LinearMIP(ref, inst)
    triv = ref.trivial_solution(inst)
    x_bar = ref.to_assignment(inst, triv)
    x = model.solve(fixed=x_bar, integer=set(), relaxed=set(), time_limit=5)
    assert ref.from_assignment(inst, x) == triv and model.last_objective == pytest.approx(ref.cost_terms(inst, triv)["distancia"])
    x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=10, near=(x_bar, 4))
    assert sum(abs(x[v] - x_bar[v]) for v in x_bar) <= 4 + 1e-6


def _ref_sources():
    from pathlib import Path

    src = Path(ref.__file__).read_text().replace("from .instance import", "from examples.cvrp.instance import")
    marker = "# ---------------------------------------------------------------- vista MIP"
    head, mip = src.split(marker)
    mip = mip.split("# ---------------------------------------------------------------- vista constructiva")[0]
    header = "from __future__ import annotations\n\nimport math\nfrom random import Random\n\n"
    return head, header + mip


def test_a_single_variable_group_is_rejected(cases):
    """Corrida 21: variable_groups con un solo grupo (partición válida) dejaba inútil a FIX_OPT."""
    report = check_mip_view(mutant(variable_groups=lambda inst: {"todo": ref.structural_variables(inst)}), cases)
    assert not report.passed and "groups_split_the_problem" in report.feedback()


def test_two_halves_of_the_variable_list_are_rejected(cases):
    """Corrida 22: la lista partida en 2 mitades pasaba el umbral del 60 %, pero FIX_OPT libera de a
    2 grupos por defecto y cada subproblema era el MIP completo."""
    def variable_groups(inst):
        xs = ref.structural_variables(inst)
        return {"g1": xs[: len(xs) // 2], "g2": xs[len(xs) // 2:]}

    report = check_mip_view(mutant(variable_groups=variable_groups), cases)
    assert not report.passed and "groups_split_the_problem" in report.feedback()


def test_an_exception_in_the_generated_parts_is_a_rejection_not_a_crash(cases):
    def violations(inst, sol):
        raise ValueError("too many values to unpack (expected 2)")

    report = check_mip_view(mutant(violations=violations), cases)
    assert not report.passed and "ValueError" in report.feedback()


def test_assignment_that_includes_auxiliaries_is_named_precisely(cases):
    """Corridas 33 y 34: 'faltan [], sobran []' cuando to_assignment traía también las auxiliares."""
    m = mutant(to_assignment=lambda inst, sol: {**ref.to_assignment(inst, sol), **ref.aux_values(inst, sol)},
               from_assignment=lambda inst, x: ref.from_assignment(inst, {k: v for k, v in x.items() if k.startswith("x_")}))
    msg = check_mip_view(m, cases).feedback()
    assert "SOLO las estructurales" in msg and "u_" in msg


def test_a_tiny_mip_time_limit_does_not_crash_cbc():
    """Con timeLimit 0.1 s CBC terminaba con error en el sub-MIP de un CVRP de 100 clientes (tuning 89): el sub-MIP usa
    al menos `MIN_MIP_SECONDS` y un error de CBC es "sin solución"."""
    from core.packs import GroupWindowDestruction
    from examples.cvrp.pack import PACK

    inst = PACK.make_instances(1, 500, PACK.parse_size("x100"))[0]
    P = PartsModel(ref, inst)
    sol = ref.trivial_solution(inst)
    _, free = GroupWindowDestruction(P).destroy(sol, 0.2, Random(0))
    x = P.to_assignment(sol)
    out = P.build_mip(inst).solve({v: val for v, val in x.items() if v not in free}, set(free), set(), 0.1, warm_start=x)
    assert out is None or P.from_assignment(out) is not None
