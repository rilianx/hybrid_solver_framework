"""Los packs del job shop y del CVRP con el modelo C++ generado: mismas instancias y casos, modelo de referencia."""

import pytest

from core.validation.model_parts import check_heuristic_view
from core.packs import base_pack


@pytest.mark.parametrize("name, ref", [("jobshop_gen", "examples.jobshop.model_parts"),
                                       ("cvrp_gen", "examples.cvrp.model_parts")])
def test_gen_pack(name, ref):
    import importlib

    pack = base_pack(name)
    assert pack.name == name and pack.handwritten and all(c["name"] in ("trivial", "random") or c["slot"] != "constructor"
                                                          for c, _ in pack.handwritten)
    assert pack.native_module == f"examples.{name}.native_parts"
    assert check_heuristic_view(importlib.import_module(ref), pack.load_cases()).passed
    inst = pack.make_instances(1, 0, pack.parse_size(pack.default_size))[0]
    assert pack.baseline_cost(inst) > 0
