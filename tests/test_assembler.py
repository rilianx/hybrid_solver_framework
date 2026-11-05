"""Pegamento §8: catálogo → ConfigSpace → configuración → variante → costo."""

from random import Random

import pytest

pytest.importorskip("pulp")

from config_space import to_irace_parameters
from core.assembler import Assembler, AssemblyError, describe
from examples.lotsizing.instance import CLSPInstance
from tests.clsp_fixtures import LotSizingModel, clsp_registry

SKELETONS = {"SA", "ILS", "TS", "VNS", "HYB"}


@pytest.fixture(scope="module")
def inst():
    return CLSPInstance.random(3, 5, Random(4))


@pytest.fixture(scope="module")
def assembler():
    return Assembler(problem_factory=LotSizingModel, registry=clsp_registry())


def test_all_skeletons_available_and_space_exports(assembler):
    assert set(assembler.available_skeletons()) == SKELETONS  # PR no: no hay relink
    txt = to_irace_parameters(assembler.config_space())
    assert 'skeleton "--skeleton=" c (' in txt and '"HYB"' in txt
    assert "all_setups" in txt and "lot_for_lot" in txt


@pytest.mark.parametrize("skeleton", sorted(SKELETONS))
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
        config = space.sample(Random(seed))
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
        assembler.assemble({"skeleton": "HYB", "constructor": "lot_for_lot", "neighborhood": "setup_flip",
                            "perturbation": "setup_flip_perturbation", "destruction": "lot_for_lot"})
