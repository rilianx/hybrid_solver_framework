"""Los packs de todos los problemas tienen la misma forma: un oráculo que pasa sus casos, las partidas trivial y al azar
y el modelo C++ generado (`native_parts`); con la vista MIP que escribió el LLM, las destrucciones genéricas de HYB."""

import importlib

import pytest

from core.packs import PACKS, base_pack
from core.validation.model_parts import check_heuristic_view


@pytest.mark.parametrize("name", sorted(PACKS))
def test_pack(name):
    pack = base_pack(name)
    assert pack.name == name and pack.native_module.endswith(".native_parts")
    assert pack.default_workspace == f"generated/{name}_native"
    by_slot = {}
    for c, _ in pack.base_components:
        by_slot.setdefault(c["slot"], []).append(c["name"])
    assert by_slot["constructor"] == ["trivial", "random"]
    parts = importlib.import_module(pack.variants[next(iter(pack.variants))][1])
    assert not hasattr(parts, "constraint_families")  # el oráculo no trae vista MIP: la escribe el LLM
    assert "destruction" not in by_slot
    assert check_heuristic_view(parts, pack.load_cases()).passed
    # el contrato del modelo C++ (hsf/generic.hpp): la solución y la respuesta son una lista de listas de enteros
    for case in pack.load_cases():
        for sc in case.solutions:
            assert all(isinstance(row, list) for row in sc["answer"]), (name, case.name)
    inst = pack.make_instances(1, 0, pack.parse_size(pack.default_size))[0]
    assert pack.baseline_cost(inst) != 0  # negativo en los de maximización (MKP: -beneficio)


def test_the_generic_destructions_pass_the_validator():
    from random import Random

    from core.packs import GroupWindowDestruction, RandomVariableDestruction, mip_path, with_generated_mip
    from core.validation import validate_component

    for name in ("clsp", "jobshop", "cvrp"):
        pack = with_generated_mip(base_pack(name), mip_path(base_pack(name)))
        assert [c["name"] for c, _ in pack.base_components if c["slot"] == "destruction"] == ["group_window", "random_variables"]
        ctx = pack.make_contexts(n_contexts=1)[0]
        for cls in (GroupWindowDestruction, RandomVariableDestruction):
            comp = {"name": cls.__name__, "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}}
            report = validate_component(comp, cls(ctx.problem), ctx)
            assert report.passed, (name, cls.__name__, report.feedback())
        _, free = GroupWindowDestruction(ctx.problem).destroy(ctx.trivial_solutions[0], 0.3, Random(0))
        assert free
