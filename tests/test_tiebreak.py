"""Slot `tiebreak` (desempate): un criterio secundario que los esqueletos C++ usan solo entre soluciones con el mismo
objetivo. Se valida (finito, determinista, distingue soluciones empatadas), entra al espacio con la opción `none` y
corre en los esqueletos que lo admiten."""

from __future__ import annotations

import shutil
from random import Random

import pytest

pytest.importorskip("pybind11")
if shutil.which("g++") is None:
    pytest.skip("sin g++", allow_module_level=True)

from tests.test_native_generation import SWAP  # noqa: E402

POSITIONS = '''```cpp
// COMPONENT: {"name": "weighted_positions", "slot": "tiebreak", "params": {}}
struct WeightedPositions : hsf::TieBreak<Model> {
    double score(const Model::Solution& s) override {
        double t = 0;
        for (size_t m = 0; m < s.size(); ++m)
            for (size_t k = 0; k < s[m].size(); ++k) t += (double)(k + 1) * (double)(s[m][k] + 1) * (double)(m + 1);
        return t;
    }
};
std::unique_ptr<hsf::TieBreak<Model>> make_component(const Model&, const Config&) {
    return std::make_unique<WeightedPositions>();
}
```'''

CONSTANT = POSITIONS.replace("weighted_positions", "constant_zero").replace("return t;", "return 0.0 * t;")


@pytest.fixture(scope="module")
def pack():
    from core.packs import base_pack

    return base_pack("jobshop")


def test_a_tiebreak_is_accepted_enters_the_space_with_none_and_runs_in_cpp(pack, tmp_path):
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog
    from tuning.cli import make_assembler

    client = ScriptedClient(responses=[SWAP, POSITIONS])
    nb, _ = generate_native_slot(client, pack, "neighborhood", 1, tmp_path, verbose=False)
    tb, stats = generate_native_slot(client, pack, "tiebreak", 1, tmp_path, verbose=False)
    assert [c.name for c in tb] == ["weighted_positions"], stats.rejections_by_layer
    assert "DESEMPATE" in client.calls[-1][1] and "hsf::TieBreak" in client.calls[-1][1]
    write_catalog(tmp_path, nb)
    write_catalog(tmp_path, tb)
    A, _ = make_assembler(pack, str(tmp_path))
    names = [c.name for c in A.registry.for_slot("tiebreak")]
    assert names[0] == "none" and "weighted_positions" in names  # sin desempate es el default
    inst = pack.make_instances(1, 0, pack.parse_size("6x4"))[0]
    P = pack.problem_factory(inst)
    for sk, extra in (("ILS", {}), ("TS", {}), ("VNS", {}), ("PR", None)):
        if sk not in A.available_skeletons():
            continue
        cfg = A.default_config(sk, {"neighborhood": "adjacent_swap", "tiebreak": "weighted_positions"})
        assert cfg["tiebreak"] == "weighted_positions"
        res = A.assemble(cfg)(inst, Random(0), 0.3)
        assert P.is_feasible(res.best_solution) and res.best_objective == pytest.approx(P.objective(res.best_solution))


def test_a_tiebreak_that_does_not_break_ties_is_rejected(pack, tmp_path):
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot

    accepted, stats = generate_native_slot(ScriptedClient(responses=[CONSTANT]), pack, "tiebreak", 1, tmp_path,
                                           max_rounds=1, verbose=False)
    assert not accepted and stats.rejections_by_layer == {"quality": 1}


def test_the_tiebreak_is_optional_in_the_skeletons_that_compare_solutions():
    """ILS, TS, VNS, PR y HYB comparan soluciones (búsqueda local, paso tabú, aceptación); SA acepta empates siempre."""
    from core.assembler import SKELETONS

    assert all("tiebreak" in SKELETONS[s].optional_slots for s in ("ILS", "TS", "VNS", "PR", "HYB"))
    assert "tiebreak" not in SKELETONS["SA"].optional_slots
