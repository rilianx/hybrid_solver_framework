"""ProblemModel del CLSP por piezas: el mecanismo de `core.model_parts` en un segundo problema, con
variables auxiliares continuas (producción e inventario) que salen de un LP y no de la solución."""

from __future__ import annotations

import types
from random import Random

import pytest

from core.model_parts import PartsModel
from core.validation.model_parts import check_heuristic_view, check_mip_optimum, check_mip_view, validate_parts
from examples.lotsizing import model_parts as ref
from examples.lotsizing.cases import brute_force_optimum, handwritten_optimum, load_cases
from examples.lotsizing.pack import PACK


@pytest.fixture(scope="module")
def cases():
    return load_cases()


@pytest.fixture(scope="module")
def scale():
    return PACK.make_instances(1, 777, PACK.parse_size(PACK.default_size))


def mutant(**overrides):
    m = types.SimpleNamespace(**{k: getattr(ref, k) for k in dir(ref) if not k.startswith("_")})
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


def test_reference_parts_pass_and_brute_force_matches_the_handwritten_mip(cases, scale):
    report = validate_parts(ref, cases, scale_instances=scale)
    assert report.passed, report.feedback()
    inst = cases[0].instance
    assert brute_force_optimum(inst)[0] == pytest.approx(cases[0].optimum, abs=1e-5)
    assert handwritten_optimum(inst) == pytest.approx(cases[0].optimum, abs=1e-4)


def test_cases_mix_feasible_and_infeasible_plans(cases):
    flags = [s["feasible"] for c in cases for s in c.solutions]
    assert any(flags) and not all(flags)


def test_skeletons_run_on_the_assembled_model_with_the_clsp_components():
    from core.assembler import Assembler
    from examples.lotsizing.catalog import build_registry

    inst = PACK.make_instances(1, 5, PACK.parse_size("5x6"))[0]
    P = PartsModel(ref, inst)
    A = Assembler(problem_factory=lambda i: PartsModel(ref, i), registry=build_registry())
    for sk in ("SA", "FIX_OPT"):
        r = A.assemble(A.default_config(sk))(inst, Random(0), 0.5)
        assert P.is_feasible(r.best_solution) and r.best_objective <= P.objective(ref.trivial_solution(inst)) + 1e-6


def test_holding_cost_on_production_instead_of_inventory_fails_against_the_cases(cases):
    def cost_terms(inst, sol):
        x, _, _ = ref._plan(inst, ref.canonical(sol))
        terms = ref.cost_terms(inst, sol)
        return {"setup": terms["setup"], "inventario": sum(inst.holding_cost[i] * v for (i, _t), v in x.items())}

    report = check_heuristic_view(mutant(cost_terms=cost_terms), cases)
    assert not report.passed and "cost_matches_cases" in report.feedback()


def test_balance_without_previous_inventory_is_named_by_family(cases):
    def constraint_families(inst):
        fams = ref.constraint_families(inst)
        # sin el término +s_{t-1}: el inventario no pasa de un período al siguiente
        fams["demanda.balance"] = [({v: c for v, c in coefs.items() if not (v.startswith("s_") and c == 1.0)}, sense, rhs)
                                   for coefs, sense, rhs in fams["demanda.balance"]]
        return fams

    report = check_mip_view(mutant(constraint_families=constraint_families), cases)
    msg = report.feedback()
    assert not report.passed and "families_agree" in msg and "demanda.balance" in msg


def test_a_mip_without_capacity_is_caught_by_the_expected_optimum(cases, scale):
    def constraint_families(inst):
        return {k: v for k, v in ref.constraint_families(inst).items() if k != "capacidad"}

    m = mutant(constraint_families=constraint_families)
    assert check_mip_view(m, cases, scale_instances=scale).passed  # punto a punto no se ve: la producción óptima nunca viola la capacidad
    report = check_mip_optimum(m, cases, time_limit=10)
    msg = report.feedback()
    assert not report.passed and ("permite soluciones" in msg or "mip_solution_feasible" in msg)


def test_group_granularity_is_measured_at_realistic_size(cases, scale):
    """En una micro-instancia de 3 períodos, 3 grupos por período es lo correcto; la lista partida en
    mitades se sigue rechazando en la instancia de tamaño realista."""
    assert check_mip_view(ref, cases, scale_instances=scale).passed
    assert "groups_split_the_problem" in check_mip_view(ref, cases).feedback()  # sin instancia realista: la regla en los casos

    def halves(inst):
        ys = ref.structural_variables(inst)
        return {"a": ys[: len(ys) // 2], "b": ys[len(ys) // 2:]}

    report = check_mip_view(mutant(variable_groups=halves), cases, scale_instances=scale)
    assert not report.passed and "tamaño realista" in report.feedback()


def test_model_spec_forbids_the_handwritten_model():
    spec = PACK.make_model_spec()
    assert "examples.lotsizing.problem_model" in spec.forbidden_modules
    assert spec.instance_import == "examples.lotsizing.instance" and "demanda" in spec.families


def test_a_free_shortage_variable_is_named_in_the_report(cases, scale):
    """Corrida 28: la vista MIP tenía variables de faltante en el balance, fuera del objetivo."""
    def variables(inst):
        out = ref.variables(inst)
        out.update({f"u_{i}_{t}": (0.0, 1e6, "continuous") for i in range(inst.n_items) for t in range(inst.n_periods)})
        return out

    def aux_values(inst, sol):
        x, s, _ = ref._plan(inst, ref.canonical(sol))
        out = ref.aux_values(inst, sol)
        for i in range(inst.n_items):
            for t in range(inst.n_periods):
                prev = s[i, t - 1] if t else 0.0
                out[f"u_{i}_{t}"] = max(0.0, inst.demand[i][t] + s[i, t] - prev - x[i, t])
        return out

    def constraint_families(inst):
        fams = ref.constraint_families(inst)
        fams["demanda.balance"] = [({**coefs, f"u_{k // inst.n_periods}_{k % inst.n_periods}": 1.0}, sense, rhs)
                                   for k, (coefs, sense, rhs) in enumerate(fams["demanda.balance"])]
        return fams

    m = mutant(variables=variables, aux_values=aux_values, constraint_families=constraint_families)
    msg = check_mip_view(m, cases, scale_instances=scale).feedback()
    assert "families_agree" in msg and "no están en el objetivo" in msg and "u_" in msg
