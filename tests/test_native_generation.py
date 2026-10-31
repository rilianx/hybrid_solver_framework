"""Componentes C++ generados por el LLM (`llm.native_generator`): un error de compilación vuelve al LLM y se
corrige, una caída del código generado es un rechazo (no tumba la generación), el prompt no trae pistas del
catálogo escrito a mano y el tuner corre el catálogo generado en C++."""

from __future__ import annotations

import importlib
import shutil

import pytest

pytest.importorskip("pybind11")
if shutil.which("g++") is None:
    pytest.skip("sin g++", allow_module_level=True)

SWAP = '''```cpp
// COMPONENT: {"name": "adjacent_swap", "slot": "neighborhood", "params": {}}
struct AdjacentSwap : hsf::Neighborhood<JobShop> {
    const JobShop& js;
    explicit AdjacentSwap(const JobShop& m) : js(m) {}
    void moves(const JobShop::Solution& s, std::vector<Move>& out) override {
        for (int mm = 0; mm < (int)s.size(); ++mm)
            for (int i = 0; i + 1 < (int)s[mm].size(); ++i) out.push_back({mm, i, 0, 0, 0, 0});
    }
    JobShop::Solution apply(const JobShop::Solution& s, const Move& m) override {
        auto t = s;
        std::swap(t[m[0]][m[1]], t[m[0]][m[1] + 1]);
        return t;
    }
    double delta(const JobShop::Solution& s, const Move& m) override { return js.objective(apply(s, m)) - js.objective(s); }
};
std::unique_ptr<hsf::Neighborhood<JobShop>> make_component(const JobShop& model, const Config&) {
    return std::make_unique<AdjacentSwap>(model);
}
```'''


@pytest.fixture(scope="module")
def pack():
    from llm.cycle import base_pack

    return base_pack("jobshop")


def test_a_compile_error_goes_back_to_the_llm_and_the_fix_is_accepted(pack, tmp_path):
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog

    broken = SWAP.replace("t[m[0]][m[1] + 1]);", "t[m[0]][m[1] + 1])")
    client = ScriptedClient(responses=[broken, SWAP])
    accepted, stats = generate_native_slot(client, pack, "neighborhood", 1, tmp_path, max_rounds=2, verbose=False)
    assert [c.name for c in accepted] == ["adjacent_swap"] and stats.rejections_by_layer == {"compile": 1}
    assert "adjacent_swap.hpp:" in client.calls[-1][1] and "error" in client.calls[-1][1]
    assert write_catalog(tmp_path, accepted).exists()


def test_a_crash_in_generated_code_is_a_rejection(pack, tmp_path):
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot

    crash = SWAP.replace("auto t = s;", "auto t = s;\n        t[m[0]][1000000] = 0;  // fuera de rango")
    accepted, stats = generate_native_slot(ScriptedClient(responses=[crash]), pack, "neighborhood", 1, tmp_path,
                                           max_rounds=1, verbose=False)
    assert not accepted and stats.rejections_by_layer == {"operational": 1}


def test_the_prompt_has_no_hints_from_the_handwritten_catalog(pack):
    from llm.native_generator import NATIVE_SYSTEM_PROMPT, generation_prompt

    gen = importlib.import_module(pack.native_module).GENERATION
    for slot in ("neighborhood", "perturbation", "greedy_score"):
        text = (NATIVE_SYSTEM_PROMPT + generation_prompt(pack, gen, slot, 3, [])).lower()
        for word in ("crític", "critical", "cabeza", "taillard", "nowicki", "n5", "bloque crít", "handwritten"):
            assert word not in text, (slot, word)


def test_the_tuner_runs_the_generated_cpp_catalog(pack, tmp_path):
    pytest.importorskip("optuna")
    import json

    from examples.jobshop.tune import main
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog

    ws = tmp_path / "ws"
    accepted, _ = generate_native_slot(ScriptedClient(responses=[SWAP]), pack, "neighborhood", 1, ws, verbose=False)
    write_catalog(ws, accepted)
    main(["--native", "--catalog", "generated", "--generated", str(ws), "--size", "6x4", "--trials", "4", "--budget", "0.1",
          "--train", "1", "--test", "1", "--seeds", "1", "--skeletons", "SA", "TS", "--out", str(tmp_path / "out")])
    out = json.loads((tmp_path / "out" / "generated.json").read_text())
    assert "adjacent_swap" in out["test"]["tuned"]["summary"]


def test_the_optimization_stage_accepts_a_faster_equivalent_version_and_rejects_a_different_one(pack, tmp_path):
    import json

    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog
    from llm.native_optimizer import optimize_native

    accepted, _ = generate_native_slot(ScriptedClient(responses=[SWAP]), pack, "neighborhood", 1, tmp_path, verbose=False)
    write_catalog(tmp_path, accepted)
    fast = SWAP.replace(
        "double delta(const JobShop::Solution& s, const Move& m) override { return js.objective(apply(s, m)) - js.objective(s); }",
        "double delta(const JobShop::Solution& s, const Move& m) override {\n"
        "        if (!has || !(s == last)) { last = s; base = js.objective(s); has = true; }\n"
        "        return js.objective(apply(s, m)) - base;\n    }\n    JobShop::Solution last; double base = 0; bool has = false;")
    wrong = fast.replace("- base;", "- base + 1.0;")
    client = ScriptedClient(responses=[wrong, fast])
    out = optimize_native(client, pack, tmp_path, rounds=2, verbose=False)
    row = out["neighborhood/adjacent_swap"]
    assert row["accepted"] and row["rounds"] == 2 and row["after"]["delta"] >= 1.5 * row["before"]["delta"]
    prompt = client.calls[0][1]
    assert "delta" in row["rejections"][0] and "delta exacto por segundo" in prompt and "paso de TS" in prompt
    assert "SA: elige un movimiento al azar" in prompt  # el prompt dice cómo usan los esqueletos el vecindario
    entry = json.loads((tmp_path / "catalog.json").read_text())[0]
    assert entry["path"].endswith("adjacent_swap_r2.hpp") and entry["path"] == row["file"]


def test_chained_passes_reoptimize_what_improved_and_show_the_profile(pack, tmp_path):
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog
    from llm.native_optimizer import _siblings, optimize_native
    from native.generated import parse_component

    accepted, _ = generate_native_slot(ScriptedClient(responses=[SWAP]), pack, "neighborhood", 1, tmp_path, verbose=False)
    write_catalog(tmp_path, accepted)
    fast = SWAP.replace(
        "double delta(const JobShop::Solution& s, const Move& m) override { return js.objective(apply(s, m)) - js.objective(s); }",
        "double delta(const JobShop::Solution& s, const Move& m) override {\n"
        "        if (!has || !(s == last)) { last = s; base = js.objective(s); has = true; }\n"
        "        return js.objective(apply(s, m)) - base;\n    }\n    JobShop::Solution last; double base = 0; bool has = false;")
    client = ScriptedClient(responses=[fast, fast])  # la segunda pasada no gana nada: se rechaza por velocidad
    out = optimize_native(client, pack, tmp_path, rounds=1, passes=3, verbose=False)
    first, second = out["neighborhood/adjacent_swap#1"], out["neighborhood/adjacent_swap#2"]
    assert first["accepted"] and not second["accepted"] and second["min_speedup"] == 1.2
    assert "neighborhood/adjacent_swap#3" not in out  # lo que no mejoró ya no se vuelve a intentar
    assert "perfil por método" in client.calls[0][1] and "delta:" in client.calls[0][1]
    # un componente del mismo slot ya optimizado se muestra como referencia
    other = parse_component(SWAP.replace('"adjacent_swap"', '"other_swap"'))
    other.path = tmp_path / "neighborhood" / "other_swap_r2.hpp"
    comp = accepted[0]
    assert [c.name for c in _siblings([comp, other], comp)] == ["other_swap"]


def test_edit_replies_apply_like_an_editor_and_fail_with_a_reason():
    from native.edits import EditError, apply_edits, find_edits, merge_reply

    src = "int a = 1;\nint b = 2;\nint c = 1;\n"
    reply = "Cambio b:\n<<<<<<< BUSCAR\nint b = 2;\n=======\nint b = 20;\n>>>>>>> REEMPLAZAR\n"
    assert find_edits(reply) == [("int b = 2;", "int b = 20;")]
    assert merge_reply(src, reply).source == "int a = 1;\nint b = 20;\nint c = 1;\n"
    with pytest.raises(EditError, match="aparece 2 veces"):
        apply_edits(src, [("= 1;", "= 3;")])
    with pytest.raises(EditError, match="no aparece"):
        apply_edits(src, [("int d", "int e")])
    assert merge_reply(src, "```cpp\nint z;\n```").mode == "full"


def test_the_optimizer_accepts_an_edit_reply(pack, tmp_path):
    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog
    from llm.native_optimizer import optimize_native

    accepted, _ = generate_native_slot(ScriptedClient(responses=[SWAP]), pack, "neighborhood", 1, tmp_path, verbose=False)
    write_catalog(tmp_path, accepted)
    old = "double delta(const JobShop::Solution& s, const Move& m) override { return js.objective(apply(s, m)) - js.objective(s); }"
    new = ("double delta(const JobShop::Solution& s, const Move& m) override {\n"
           "        if (!has || !(s == last)) { last = s; base = js.objective(s); has = true; }\n"
           "        return js.objective(apply(s, m)) - base;\n    }\n    JobShop::Solution last; double base = 0; bool has = false;")
    bad = "<<<<<<< BUSCAR\nno existe\n=======\nx\n>>>>>>> REEMPLAZAR"
    good = f"Cacheo el objetivo:\n<<<<<<< BUSCAR\n{old}\n=======\n{new}\n>>>>>>> REEMPLAZAR"
    client = ScriptedClient(responses=[bad, good])
    row = optimize_native(client, pack, tmp_path, rounds=2, verbose=False)["neighborhood/adjacent_swap"]
    assert row["accepted"] and row["reply_modes"] == ["edits"] and row["edit_failures"] == 1
    assert "no se pudo aplicar" in client.calls[1][1] and "BUSCAR" in client.calls[0][1]


RELINK = '''```cpp
// COMPONENT: {"name": "adjacent_order_relink", "slot": "relink", "params": {}}
struct OrderRelink : hsf::Relink<JobShop> {
    const JobShop& js;
    explicit OrderRelink(const JobShop& m) : js(m) {}
    static int pos(const std::vector<int>& v, int x) { return (int)(std::find(v.begin(), v.end(), x) - v.begin()); }
    int distance(const JobShop::Solution& a, const JobShop::Solution& b) override {
        int d = 0;
        for (size_t mm = 0; mm < a.size(); ++mm)
            for (size_t i = 0; i < a[mm].size(); ++i)
                for (size_t k = i + 1; k < a[mm].size(); ++k) d += pos(b[mm], a[mm][i]) > pos(b[mm], a[mm][k]);
        return d;
    }
    JobShop::Solution step(const JobShop::Solution& cur, const JobShop::Solution& guide, Rng& rng) override {
        std::vector<std::pair<int, int>> inv;
        for (size_t mm = 0; mm < cur.size(); ++mm)
            for (size_t i = 0; i + 1 < cur[mm].size(); ++i)
                if (pos(guide[mm], cur[mm][i]) > pos(guide[mm], cur[mm][i + 1])) inv.push_back({(int)mm, (int)i});
        if (inv.empty()) return cur;
        auto [mm, i] = inv[rng.below((int)inv.size())];
        auto t = cur;
        std::swap(t[mm][i], t[mm][i + 1]);
        return t;
    }
};
std::unique_ptr<hsf::Relink<JobShop>> make_component(const JobShop& model, const Config&) {
    return std::make_unique<OrderRelink>(model);
}
```'''


def test_a_generated_relink_runs_in_pr(pack, tmp_path):
    from random import Random

    from llm import ScriptedClient
    from llm.native_generator import generate_native_slot, write_catalog
    from tuning.cli import make_assembler

    client = ScriptedClient(responses=[SWAP, RELINK])
    nb, _ = generate_native_slot(client, pack, "neighborhood", 1, tmp_path, verbose=False)
    rel, _ = generate_native_slot(client, pack, "relink", 1, tmp_path, verbose=False)
    assert [c.name for c in rel] == ["adjacent_order_relink"]
    assert "Relink" in client.calls[-1][1] and "path relinking" in client.calls[-1][1]
    write_catalog(tmp_path, nb)
    write_catalog(tmp_path, rel)
    A, _ = make_assembler(pack, "generated", str(tmp_path), native=True)
    assert "PR" in A.available_skeletons()
    cfg = A.default_config("PR", {"neighborhood": "adjacent_swap", "relink": "adjacent_order_relink", "constructor": "random"})
    cfg.update({"PR.pop_size": 3, "PR.ts_iters": 50})
    inst = pack.make_instances(1, 0, pack.parse_size("5x4"))[0]
    res = A.assemble(cfg)(inst, Random(0), 0.3)
    assert pack.problem_factory(inst).is_feasible(res.best_solution)
