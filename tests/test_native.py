"""Backend nativo (C++): el job shop en C++ pasa el mismo validador y los mismos casos que las piezas de
Python, coincide con ellas en costo y violaciones, y una configuración del tuner corre entera en C++."""

from __future__ import annotations

import shutil
from random import Random

import pytest

pytest.importorskip("pybind11")
if shutil.which("g++") is None:
    pytest.skip("sin g++", allow_module_level=True)


@pytest.fixture(scope="module")
def nat():
    from examples.jobshop import native_parts

    return native_parts


def test_the_native_parts_pass_the_model_validator_with_the_same_cases(nat):
    from core.validation.model_parts import check_construction_view, validate_parts
    from examples.jobshop.cases import load_cases
    from examples.jobshop.instance import JSSPInstance

    cases = load_cases()
    scale = [JSSPInstance.random(10, 10, Random(777))]
    assert validate_parts(nat, cases, scale_instances=scale).passed
    assert check_construction_view(nat, cases, scale_instances=scale).passed


def test_native_and_python_agree_on_cost_and_violations(nat):
    from examples.jobshop import model_parts as py
    from examples.jobshop.instance import JSSPInstance

    for s in range(60):
        inst = JSSPInstance.random(Random(s).randint(2, 7), Random(s + 1).randint(2, 5), Random(s))
        rng = Random(s)
        base = py.random_solution(inst, rng)
        for sol in (base, tuple(tuple(rng.sample(list(q), len(q))) for q in base), (base[0][1:],) + base[1:]):
            assert nat.violations(inst, sol) == py.violations(inst, sol)
            assert nat.cost_terms(inst, sol) == py.cost_terms(inst, sol)


def test_the_native_components_pass_the_component_validator(nat):
    from core.validation import validate_component
    from examples.jobshop.native_catalog import native_handwritten
    from examples.jobshop.pack import _BASE, make_model_spec
    from llm.cycle import parts_pack

    pack = parts_pack(_BASE, nat, "examples.jobshop.native_parts", make_model_spec(), "jobshop_native")
    pack.handwritten = native_handwritten()
    ctx = pack.make_contexts()[0]
    for comp, factory in pack.handwritten:
        if comp["slot"] in ("constructor", "neighborhood", "perturbation"):
            report = validate_component(comp, factory(ctx.problem), ctx)
            assert report.passed, (comp["name"], report.feedback())


@pytest.mark.parametrize("skeleton", ["SA", "ILS", "VNS", "TS"])
def test_a_tuner_configuration_runs_entirely_in_cpp(nat, skeleton):
    from core.native_runner import NativeRunner
    from examples.jobshop.pack import PACK
    from tuning.cli import make_assembler

    A, _ = make_assembler(PACK, "handwritten")
    runner = NativeRunner(A, nat.native, nat.model)
    cfg = A.default_config(skeleton)
    cfg["constructor"] = "greedy_most_work_remaining"
    inst = PACK.make_instances(1, 3, PACK.parse_size("8x5"))[0]
    P = PACK.problem_factory(inst)
    start = P.objective(PACK.baseline_constructor().build(inst, Random(0)))
    res = runner.assemble(cfg)(inst, Random(0), 0.2)
    assert P.is_feasible(res.best_solution) and res.best_objective == pytest.approx(P.objective(res.best_solution))
    assert res.best_objective < start and res.iterations > 0


def test_a_compile_error_is_reported_with_the_compiler_output(tmp_path):
    from native.build import NativeBuildError, build

    src = tmp_path / "broken.cpp"
    src.write_text("int main( { return 0; }\n")
    with pytest.raises(NativeBuildError, match="broken.cpp"):
        build("broken", src)


def test_the_tuner_runs_natively(tmp_path):
    pytest.importorskip("optuna")
    import json

    from examples.jobshop.tune import main

    main(["--native", "--catalog", "handwritten", "--size", "6x4", "--trials", "6", "--budget", "0.1", "--train", "1",
          "--test", "1", "--seeds", "1", "--out", str(tmp_path)])
    out = json.loads((tmp_path / "handwritten.json").read_text())
    assert out["settings"]["native"] is True
    assert out["test"]["tuned"]["summary"].split("[")[0] in ("SA", "ILS", "VNS", "TS")
