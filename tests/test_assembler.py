"""Pegamento §8: catálogo → ConfigSpace → configuración → variante → costo, incluyendo
componentes "generados" que entran al catálogo y aparecen en el espacio."""

from random import Random

import pytest

pytest.importorskip("pulp")

from config_space import suggest_from_space, to_irace_parameters
from core.assembler import Assembler, AssemblyError, describe
from examples.lotsizing.catalog import build_registry, load_generated
from examples.lotsizing.llm_spec import make_contexts, make_spec
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel
from examples.lotsizing.random_search import RandomTrial
from llm import ScriptedClient, generate_slot, register_generated
from tests.test_llm_generation import GOOD_SHIFT, fence


@pytest.fixture(scope="module")
def inst():
    return CLSPInstance.random(3, 5, Random(4))


@pytest.fixture(scope="module")
def assembler():
    return Assembler(problem_factory=LotSizingModel, registry=build_registry())


def test_all_skeletons_available_and_space_exports(assembler):
    assert set(assembler.available_skeletons()) == {"SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH"}
    space = assembler.config_space()
    txt = to_irace_parameters(space)
    assert 'skeleton "--skeleton=" c (' in txt and '"LOCAL_BRANCH"' in txt
    assert "sliding_window.window_size" in txt and 'fixing_policy == "sliding_window"' in txt


@pytest.mark.parametrize("skeleton", ["SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH"])
def test_default_config_of_each_skeleton_runs(assembler, inst, skeleton):
    config = assembler.default_config(skeleton)
    runner = assembler.assemble(config)
    result = runner(inst, Random(0), budget=1.0)
    assert LotSizingModel(inst).is_feasible(result.best_solution)
    assert result.iterations >= 1
    assert skeleton in describe(config)


def test_sampled_configs_assemble_and_evaluate(assembler, inst):
    space = assembler.config_space()
    seen = set()
    for seed in range(12):
        config = suggest_from_space(space, RandomTrial(Random(seed)))
        seen.add(config["skeleton"])
        cost = assembler.evaluate(config, [inst], budget=0.5, seed=0, on_error="raise")
        assert cost < assembler.penalty_cost
    assert len(seen) >= 3  # el muestreo recorre varios esqueletos


def test_evaluate_penalizes_bad_config(assembler, inst):
    bad = {"skeleton": "SA", "constructor": "lot_for_lot", "neighborhood": "no_existe"}
    assert assembler.evaluate(bad, [inst], budget=0.5) == assembler.penalty_cost
    with pytest.raises((AssemblyError, KeyError)):
        assembler.assemble(bad)


def test_incompatible_component_rejected(assembler):
    bad = {"skeleton": "SA", "constructor": "lot_for_lot", "neighborhood": "setup_flip", "perturbation": "x"}
    assembler.assemble(bad)  # perturbation no es slot de SA: se ignora
    with pytest.raises(AssemblyError):
        assembler.assemble({"skeleton": "FIX_OPT", "constructor": "lot_for_lot", "fixing_policy": "setup_flip"})


def test_generated_component_enters_catalog_and_space(inst, tmp_path):
    # strict=False: este test cubre la admisión al catálogo, no el empuje del modo generación
    spec, contexts = make_spec(), make_contexts(n_contexts=1, n_items=2, n_periods=4, strict=False)
    accepted, _ = generate_slot(ScriptedClient([fence(GOOD_SHIFT)]), spec, "neighborhood", 1, contexts, tmp_path, verbose=False)
    registry = build_registry(accepted)
    assert registry.get("neighborhood", "shift_setup_earlier").is_compatible_with("SA")

    assembler = Assembler(problem_factory=LotSizingModel, registry=registry)
    node = next(n for n in assembler.config_space().nodes if n.name == "neighborhood")
    assert set(node.values) == {"setup_flip", "shift_setup_earlier"}

    config = assembler.default_config("SA", choices={"neighborhood": "shift_setup_earlier"})
    result = assembler.assemble(config)(inst, Random(0), budget=1.0)
    assert LotSizingModel(inst).is_feasible(result.best_solution)

    # y se puede recargar desde disco (revalidando) para una sesión posterior
    reloaded = load_generated(tmp_path, revalidate=True, verbose=False)
    assert [c.name for c in reloaded] == ["shift_setup_earlier"]
    assert register_generated(build_registry(), reloaded) == ["shift_setup_earlier"]
