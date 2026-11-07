"""Backend nativo (C++) con lo que escribió el LLM para el job shop (`generated/jobshop_native/`): el modelo C++ pasa
el mismo validador y los mismos casos que las piezas de Python y coincide con ellas en las familias violadas y en el
costo de las factibles, y cada
esqueleto corre entero en C++ (y en Python, con los mismos componentes) con el catálogo generado."""

from __future__ import annotations

import shutil
from random import Random

import pytest

pytest.importorskip("pybind11")
if shutil.which("g++") is None:
    pytest.skip("sin g++", allow_module_level=True)

from examples.jobshop import model_parts as py  # noqa: E402
from examples.jobshop.instance import JSSPInstance  # noqa: E402
from examples.jobshop.pack import PACK  # noqa: E402


@pytest.fixture(scope="module")
def assembler():
    from tuning.cli import make_assembler

    return make_assembler(PACK)[0]


@pytest.fixture(scope="module")
def nat(assembler):
    from native.generic_model import model_parts

    return model_parts(assembler.native, py, assembler.model_of)


def test_the_generated_model_passes_the_model_validator_with_the_same_cases(nat):
    from core.validation.model_parts import validate_parts
    from examples.jobshop.cases import load_cases

    from pathlib import Path

    from core.packs import load_mip, with_mip

    parts = with_mip(nat, load_mip(Path("generated/jobshop_native/mip/mip.py")))  # con la vista MIP generada
    assert validate_parts(parts, load_cases(), scale_instances=[JSSPInstance.random(10, 10, Random(777))]).passed


def test_the_generated_model_and_python_agree_on_cost_and_violations(nat):
    for s in range(40):
        inst = JSSPInstance.random(Random(s).randint(2, 7), Random(s + 1).randint(2, 5), Random(s))
        rng = Random(s)
        base = py.random_solution(inst, rng)
        for sol in (base, tuple(tuple(rng.sample(list(q), len(q))) for q in base), (base[0][1:],) + base[1:]):
            violated = {k for k, v in py.violations(inst, sol).items() if v > 0}
            assert {k for k, v in nat.violations(inst, sol).items() if v > 0} == violated
            if not violated:  # en una infactible el costo es arbitrario (lo mismo exige native/check_model.py)
                assert nat.cost_terms(inst, sol) == pytest.approx(py.cost_terms(inst, sol))


def _check(A, cfg, inst, budget=0.3, python=False):
    from core.assembler import Assembler

    run = Assembler.assemble(A, cfg) if python else A.assemble(cfg)
    res = run(inst, Random(0), budget)
    P = PACK.problem_factory(inst)
    assert P.is_feasible(res.best_solution) and res.best_objective == pytest.approx(P.objective(res.best_solution))
    assert res.best_objective <= P.objective(py.trivial_solution(inst)) and res.iterations > 0
    return res


@pytest.mark.parametrize("skeleton", ["SA", "ILS", "VNS", "TS", "PR", "HYB", "GRASP"])
def test_each_skeleton_runs_entirely_in_cpp_with_the_generated_catalog(assembler, skeleton):
    assert skeleton in assembler.available_skeletons()
    cfg = assembler.default_config(skeleton)
    if skeleton == "PR":
        cfg.update({"PR.pop_size": 4, "PR.ts_iters": 100})
    _check(assembler, cfg, PACK.make_instances(1, 3, PACK.parse_size("8x5"))[0], budget=1.0 if skeleton == "HYB" else 0.3)


@pytest.mark.parametrize("variant", ["ILS anneal", "PR ils", "TS estimate", "penalty", "GRASP full"])
def test_skeleton_variants_run_in_python_and_in_cpp(assembler, variant):
    inst = PACK.make_instances(1, 3, PACK.parse_size("6x5"))[0]
    for python in (False, True):
        if variant == "ILS anneal":
            cfg = dict(assembler.default_config("ILS"), **{"ILS.accept": "anneal", "ILS.T_rel": 0.01})
        elif variant == "PR ils":
            cfg = dict(assembler.default_config("PR"), **{"PR.improve": "ils", "PR.pop_size": 4, "PR.ts_iters": 20, "PR.T_rel": 0.01})
        elif variant == "GRASP full":  # varios arranques con el constructor GRASP del LLM y primera mejora completa
            cfg = dict(assembler.default_config("GRASP"), **{"GRASP.ls_scope": "full", "GRASP.ls_strategy": "first"})
        elif variant == "TS estimate":
            cfg = dict(assembler.default_config("TS"), **{"TS.estimate_top": 3, "TS.elite_size": 4, "TS.stall": 20})
        else:  # peso bajo de las violaciones: pasa por infactibles pero devuelve la mejor factible (solo en C++)
            if python:
                continue
            cfg = dict(assembler.default_config("TS"), **{"TS.pen_adapt": "yes", "TS.pen_scale": 1e-4})
        _check(assembler, cfg, inst, python=python)


def test_a_compile_error_is_reported_with_the_compiler_output(tmp_path):
    from native.build import NativeBuildError, build

    src = tmp_path / "broken.cpp"
    src.write_text("int main( { return 0; }\n")
    with pytest.raises(NativeBuildError, match="broken.cpp"):
        build("broken", src)


def test_hyb_runs_when_the_space_has_only_hyb():
    """`--skeletons HYB`: el ILS interno de HYB toma sus defaults aunque ILS no esté en el espacio (tunings 84–86)."""
    from tuning.cli import make_assembler

    A, _ = make_assembler(PACK, skeletons=["HYB"])
    assert A.available_skeletons() == ["HYB"]
    _check(A, A.default_config("HYB"), PACK.make_instances(1, 3, PACK.parse_size("8x5"))[0], budget=1.0)
