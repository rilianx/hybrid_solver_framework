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
