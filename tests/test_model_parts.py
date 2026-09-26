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


def test_assembled_model_is_a_problem_model_the_skeletons_can_use(cases):
    from core.assembler import Assembler
    from examples.cvrp.catalog import build_registry

    inst = cases[3].instance
    P = PartsModel(ref, inst)
    triv = ref.trivial_solution(inst)
    assert P.is_feasible(triv) and P.objective(triv) == pytest.approx(ref.cost_terms(inst, triv)["distancia"])
    bad = ref.from_answer(inst, [list(inst.customers)[1:]])
    assert not P.is_feasible(bad) and P.objective(bad) > P.objective(triv)
    # los componentes del CVRP usan la misma representación canónica: corren sobre el modelo ensamblado
    A = Assembler(problem_factory=lambda i: PartsModel(ref, i), registry=build_registry())
    for sk in ("SA", "LNS_MIP"):
        r = A.assemble(A.default_config(sk))(inst, Random(0), 0.5)
        assert P.is_feasible(r.best_solution) and r.best_objective <= P.objective(triv) + 1e-6


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


def test_parts_generation_runs_both_stages_with_localized_feedback(tmp_path):
    from examples.cvrp.pack import PACK
    from llm import ScriptedClient
    from llm.parts_generator import generate_problem_model_parts

    heur, mip = _ref_sources()
    broken = heur.replace('return {"visita": float(visit), "capacidad": float(cap)}', 'return {"visita": float(visit)}')
    client = ScriptedClient(responses=[f"```python\n{broken}\n```", f"```python\n{heur}\n```", f"```python\n{mip}\n```"])
    res = generate_problem_model_parts(client, PACK.make_model_spec(), load_cases(), tmp_path, verbose=False,
                                       construction=False)
    assert res.path is not None and res.heuristic.rounds == 2 and res.mip.rounds == 1 and res.llm_calls == 3
    assert "capacidad" in res.heuristic.reports[0]
    # el prompt de la etapa MIP trae la vista heurística aprobada, no la rota
    assert heur.strip()[:200] in client.calls[2][1] and "Casos de ejemplo" in client.calls[2][1]
    # el prompt de corrección de la etapa 1 trae el reporte con la familia esperada
    assert "RECHAZADA" in client.calls[1][1] and "capacidad" in client.calls[1][1]


def test_parts_generation_forbids_importing_the_reference_parts(tmp_path):
    from examples.cvrp.pack import PACK
    from llm import ScriptedClient
    from llm.parts_generator import generate_problem_model_parts

    cheat = "from examples.cvrp.model_parts import *\n"
    client = ScriptedClient(responses=[f"```python\n{cheat}\n```"] * 2)
    res = generate_problem_model_parts(client, PACK.make_model_spec(), load_cases(), tmp_path, max_rounds=2, verbose=False)
    assert res.path is None and "no_forbidden_imports" in res.heuristic.reports[0]


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


def test_mip_stage_may_not_redefine_heuristic_names():
    """Corrida 25: la vista MIP redefinió un auxiliar de la heurística y rompió violations."""
    from llm.parts_generator import redefined_names

    heur = "def _flow(g):\n    return 1, 2\n\ndef violations(inst, sol):\n    return {}\n"
    mip = "import math\n\ndef _flow(g):\n    return 1, 2, 3\n\ndef variables(inst):\n    return {}\n"
    assert redefined_names(heur, mip) == ["_flow"]
    assert redefined_names(heur, "def _flow2(g):\n    return 0\n") == []


def test_an_exception_in_the_generated_parts_is_a_rejection_not_a_crash(cases):
    def violations(inst, sol):
        raise ValueError("too many values to unpack (expected 2)")

    report = check_mip_view(mutant(violations=violations), cases)
    assert not report.passed and "ValueError" in report.feedback()


def test_identical_copies_are_not_redefinitions():
    from llm.parts_generator import redefined_names

    heur = "def canonical(sol):\n    return tuple(sol)\n"
    assert redefined_names(heur, "def canonical(sol):\n    return tuple(sol)\n") == []
    assert redefined_names(heur, "def canonical(sol):\n    return sorted(sol)\n") == ["canonical"]
