"""El modelo C++ escrito por el LLM (`llm.native_model_generator`, contrato en `native/include/hsf/generic.hpp`): un
modelo correcto se acepta, uno con un error se rechaza con el caso que falla y se corrige, y sobre el modelo aceptado
se generan componentes y corren los esqueletos."""

from __future__ import annotations

import shutil
from random import Random

import pytest

pytest.importorskip("pybind11")
if shutil.which("g++") is None:
    pytest.skip("sin g++", allow_module_level=True)

MODEL = '''Un CVRP por rutas.
```cpp
#pragma once
#include <hsf/core.hpp>
#include <cmath>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace gen {
struct Model {
    using Solution = std::vector<std::vector<int>>;
    int n = 0;
    double Q = 0, penalty = 0;
    bool rounded = false;
    std::vector<double> x, y, d, D;
    mutable std::vector<int> seen;
    double dist(int i, int j) const { return D[(size_t)i * (n + 1) + j]; }
    static Model parse(const std::string& text) {
        std::istringstream in(text);
        std::string head;
        std::getline(in, head);
        std::istringstream hs(head);
        Model m;
        std::string flag;
        hs >> m.n >> m.Q >> flag;
        m.rounded = flag == "round";
        m.x.resize(m.n + 1), m.y.resize(m.n + 1), m.d.resize(m.n + 1);
        for (int i = 0; i <= m.n; ++i) in >> m.x[i] >> m.y[i] >> m.d[i];
        m.D.assign((size_t)(m.n + 1) * (m.n + 1), 0.0);
        for (int i = 0; i <= m.n; ++i)
            for (int j = 0; j <= m.n; ++j) {
                double v = std::hypot(m.x[i] - m.x[j], m.y[i] - m.y[j]);
                m.D[(size_t)i * (m.n + 1) + j] = m.rounded ? std::floor(v + 0.5) : v;
            }
        m.seen.assign(m.n + 1, 0);
        double t = 0;
        for (int c = 1; c <= m.n; ++c) t += 2 * m.dist(0, c);
        m.penalty = 10.0 * (t + 1.0);
        return m;
    }
    Solution trivial() const {
        Solution s;
        for (int c = 1; c <= n; ++c) s.push_back({c});
        return s;
    }
    Solution random(hsf::Rng& rng) const {
        std::vector<int> cs;
        for (int c = 1; c <= n; ++c) cs.push_back(c);
        std::shuffle(cs.begin(), cs.end(), rng.g);
        Solution s(1);
        double load = 0;
        for (int c : cs) {
            if (!s.back().empty() && load + d[c] > Q) s.emplace_back(), load = 0;
            s.back().push_back(c), load += d[c];
        }
        return s;
    }
    void eval(const Solution& s, double& visit, double& cap, double& dist_) const {
        std::fill(seen.begin(), seen.end(), 0);
        visit = cap = dist_ = 0;
        int bad = 0;
        for (auto& r : s) {
            double load = 0;
            int prev = 0;
            for (int c : r) {
                if (c < 1 || c > n) { ++bad; continue; }
                ++seen[c], load += d[c], dist_ += dist(prev, c), prev = c;
            }
            dist_ += dist(prev, 0);
            cap += std::max(0.0, load - Q);
        }
        for (int c = 1; c <= n; ++c) visit += std::abs(seen[c] - 1);
        visit += bad;
    }
    void violations(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double v, c, t;
        eval(s, v, c, t);
        out.push_back({"visita", v});
        out.push_back({"capacidad", c});
    }
    void cost_terms(const Solution& s, std::vector<std::pair<std::string, double>>& out) const {
        double v, c, t;
        eval(s, v, c, t);
        out.push_back({"distancia", t});
    }
    double objective(const Solution& s) const {
        double v, c, t;
        eval(s, v, c, t);
        return t + penalty * (v + c);
    }
    bool feasible(const Solution& s) const {
        double v, c, t;
        eval(s, v, c, t);
        return v == 0 && c <= 1e-9;
    }
};
}  // namespace gen
```'''

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


def test_a_generated_model_is_validated_corrected_and_used(tmp_path):
    from dataclasses import replace

    from llm import ScriptedClient
    from core.packs import base_pack
    from llm.native_generator import generate_native_slot, write_catalog
    from llm.native_model_generator import generate_native_model
    from native.generic_model import generation

    pack = base_pack("cvrp")
    wrong = MODEL.replace("dist_ += dist(prev, 0);", "")  # se olvida la vuelta al depósito
    client = ScriptedClient(responses=[wrong, "<<<<<<< BUSCAR\n            cap += std::max(0.0, load - Q);\n=======\n"
                                              "            dist_ += dist(prev, 0);\n            cap += std::max(0.0, load - Q);\n"
                                              ">>>>>>> REEMPLAZAR"])
    stats = generate_native_model(client, pack, tmp_path, rounds=2, verbose=False)
    assert stats["accepted"] and stats["rounds"] == 2 and stats["reply_modes"] == ["full", "edits"]
    assert "dist(prev" not in client.calls[0][1] and "generic.hpp" in client.calls[0][1]  # no ve un modelo escrito
    assert "cost_matches_cases" in stats["rejections"][0]  # el costo no coincide con el de los casos
    assert (tmp_path / "model" / "model.hpp").exists()

    # componentes y esqueletos sobre el modelo generado
    gen = generation(tmp_path / "model", "examples.cvrp.model_parts")
    gpack = replace(pack, native_module="")
    import types
    import sys
    mod = types.ModuleType("_gen_cvrp_native")
    mod.GENERATION = gen
    sys.modules["_gen_cvrp_native"] = mod
    gpack = replace(pack, native_module="_gen_cvrp_native")
    acc, st = generate_native_slot(ScriptedClient(responses=[RELOCATE]), gpack, "neighborhood", 1, tmp_path, verbose=False)
    assert [c.name for c in acc] == ["relocate_any"], st.rejections_by_layer
    write_catalog(tmp_path, acc)
    from tuning.cli import make_assembler

    A, _ = make_assembler(gpack, "generated", str(tmp_path), native=True)
    cfg = A.default_config("SA", {"neighborhood": "relocate_any", "constructor": "random"})
    inst = pack.make_instances(1, 0, pack.parse_size("15"))[0]
    res = A.assemble(cfg)(inst, Random(0), 0.3)
    assert pack.problem_factory(inst).is_feasible(res.best_solution)


def test_model_optimizer_rejects_changed_outputs_and_no_speedup(tmp_path):
    from llm import ScriptedClient
    from core.packs import base_pack
    from llm.native_model_generator import generate_native_model
    from llm.native_model_optimizer import optimize_model

    pack = base_pack("cvrp")
    assert generate_native_model(ScriptedClient(responses=[MODEL]), pack, tmp_path, rounds=1, verbose=False)["accepted"]
    accepted = (tmp_path / "model" / "model.hpp").read_text()
    wrong = ("<<<<<<< BUSCAR\n        return t + penalty * (v + c);\n=======\n        return t + 0.5 * penalty * (v + c);\n"
             ">>>>>>> REEMPLAZAR")
    same = "<<<<<<< BUSCAR\n0.5 * penalty\n=======\npenalty\n>>>>>>> REEMPLAZAR"  # (sobre la rechazada) deshace el error
    out = optimize_model(ScriptedClient(responses=[wrong, same]), pack, tmp_path, rounds=2, passes=1, verbose=False)
    row = out["passes"][0]
    assert not row["accepted"] and row["rejections"][0].split("]")[0] in ("[coherence", "[equivalence"), row["rejections"][0]
    assert row["rejections"][1].startswith("[speed]")
    assert (tmp_path / "model" / "model.hpp").read_text() == accepted  # el aceptado no cambió


def test_generation_prompt_includes_researcher_hint():
    import importlib

    from examples.flowshop.pack import PACK
    from llm.native_generator import generation_prompt

    gen = importlib.import_module(PACK.native_module).GENERATION
    text = generation_prompt(PACK, gen, "neighborhood", 2, [], None, hint="vecindarios acotados")
    assert "# Indicación del investigador\nvecindarios acotados" in text
    assert "Indicación del investigador" not in generation_prompt(PACK, gen, "neighborhood", 2, [], None)
