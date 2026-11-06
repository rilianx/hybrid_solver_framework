"""El modelo C++ del Model (rutas): mismas violaciones y costo que las piezas de Python, las
instancias X de Uchoa con distancias redondeadas, y un componente C++ generado (simulado) que se valida y corre."""

from __future__ import annotations

import shutil
from random import Random

import pytest

pytest.importorskip("pybind11")
if shutil.which("g++") is None:
    pytest.skip("sin g++", allow_module_level=True)

from examples.cvrp import model_parts as py  # noqa: E402
from examples.cvrp.instance import CVRPInstance  # noqa: E402
from examples.cvrp.pack import PACK  # noqa: E402


def _broken(sol):
    r = [list(x) for x in sol]
    dup = [list(x) for x in sol]
    dup[0].append(dup[-1][0])
    miss = [list(x) for x in sol]
    miss[0].pop()
    return [tuple(map(tuple, x)) for x in (dup, miss)] + [tuple(map(tuple, [*r, []]))]


@pytest.fixture(scope="module")
def nat():
    from native.generic_model import model_parts
    from tuning.cli import make_assembler

    A = make_assembler(PACK)[0]
    return model_parts(A.native, py, A.model_of)


def test_native_model_matches_python(nat):
    insts = PACK.make_instances(2, 11, PACK.parse_size("8")) + PACK.make_instances(2, 5, PACK.parse_size("30"))
    for inst in insts:
        sols = [py.trivial_solution(inst)] + [py.random_solution(inst, Random(s)) for s in range(10)]
        sols += [nat.random_solution(inst, Random(s)) for s in range(5)]
        for s in sols + [b for s in sols for b in _broken(s)]:
            violated = {k for k, v in py.violations(inst, s).items() if v > 1e-9}
            assert {k for k, v in nat.violations(inst, s).items() if v > 1e-9} == violated
            if not violated:
                assert nat.cost_terms(inst, s)["distancia"] == pytest.approx(py.cost_terms(inst, s)["distancia"])


def test_uchoa_instances_round_distances(nat):
    import json
    from pathlib import Path

    d = Path("examples/cvrp/uchoa")
    bk = json.loads((d / "best_known.json").read_text())
    assert len([k for k in bk if not k.startswith("_")]) == 100 and bk["X-n101-k25"] == 27591
    inst = CVRPInstance.load(str(d / "X-n101-k25.vrp"))
    assert inst.rounded and inst.n_customers == 100 and inst.capacity == 206 and inst.demand[0] == 0
    assert CVRPInstance.parse(inst.to_text()) == inst
    s = py.trivial_solution(inst)
    assert nat.cost_terms(inst, s)["distancia"] == py.cost_terms(inst, s)["distancia"] == sum(2 * inst.dist(0, c) for c in inst.customers)
    assert all(inst.dist(0, c) == int(inst.dist(0, c)) for c in inst.customers)


RELOCATE = '''```cpp
// COMPONENT: {"name": "relocate_any", "slot": "neighborhood", "params": {}}
struct RelocateAny : hsf::Neighborhood<Model> {
    const Model& v;
    explicit RelocateAny(const Model& m) : v(m) {}
    void moves(const Model::Solution& s, std::vector<Move>& out) override {
        for (int a = 0; a < (int)s.size(); ++a)
            for (int i = 0; i < (int)s[a].size(); ++i)
                for (int b = 0; b <= (int)s.size(); ++b)
                    for (int j = 0; j <= (b < (int)s.size() ? (int)s[b].size() : 0); ++j)
                        if (a != b || (j != i && j != i + 1)) out.push_back({a, i, b, j, 0, 0});
    }
    Model::Solution apply(const Model::Solution& s, const Move& m) override {
        auto t = s;
        int c = t[m[0]][m[1]];
        t[m[0]].erase(t[m[0]].begin() + m[1]);
        int j = m[3];
        if (m[2] == (int)t.size()) t.push_back({c});
        else {
            if (m[2] == m[0] && j > m[1]) --j;
            t[m[2]].insert(t[m[2]].begin() + j, c);
        }
        Model::Solution out;
        for (auto& r : t) if (!r.empty()) out.push_back(r);
        return out;
    }
    double delta(const Model::Solution& s, const Move& m) override { return v.objective(apply(s, m)) - v.objective(s); }
};
std::unique_ptr<hsf::Neighborhood<Model>> make_component(const Model& model, const Config&) {
    return std::make_unique<RelocateAny>(model);
}
```'''


def test_a_generated_cvrp_neighborhood_is_validated_and_runs(tmp_path):
    from llm import ScriptedClient
    from core.packs import base_pack
    from llm.native_generator import generate_native_slot, write_catalog
    from tuning.cli import make_assembler

    pack = base_pack("cvrp")
    client = ScriptedClient(responses=[RELOCATE])
    acc, stats = generate_native_slot(client, pack, "neighborhood", 1, tmp_path, verbose=False)
    assert [c.name for c in acc] == ["relocate_any"], stats.rejections_by_layer
    assert "struct Model" in client.calls[0][1]
    write_catalog(tmp_path, acc)
    A, _ = make_assembler(pack, str(tmp_path))
    cfg = A.default_config("SA", {"neighborhood": "relocate_any", "constructor": "random"})
    inst = pack.make_instances(1, 0, pack.parse_size("20"))[0]
    res = A.assemble(cfg)(inst, Random(0), 0.3)
    assert pack.problem_factory(inst).is_feasible(res.best_solution)
