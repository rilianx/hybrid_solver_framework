"""Prompts compactos (`--compact-prompts`, `llm/outline.py`): el modelo C++ y los componentes del catálogo como
prototipos, la instancia con sus campos y su formato; por defecto, los prompts no cambian."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from core.packs import base_pack
from llm import outline

PROBLEMS = ["flowshop", "flowshop_cmax", "clsp", "jobshop", "cvrp"]


def _methods(src: str) -> set[str]:
    return set(re.findall(r"^\s+(?:static\s+|inline\s+)*[\w:<>,\s&*]+?\b(\w+)\([^;{]*\)\s*(?:const\s*)?(?:override\s*)?\{",
                          src, re.M))


@pytest.mark.parametrize("problem", PROBLEMS)
def test_the_model_outline_keeps_every_declaration_and_drops_the_bodies(problem):
    src = Path(f"generated/{problem}_native/model/model.hpp").read_text()
    out = outline.cpp_outline(src)
    assert len(out) < len(src) / 2
    for name in _methods(src):
        assert re.search(rf"\b{name}\(", out), name
    assert out.count("{") == out.count("}") and "for (" not in out and "return " not in out
    assert "struct Model" in out and "objective(" in out and "violations(" in out


def test_the_outline_skips_braces_in_strings_and_comments():
    src = 'struct A {\n  int f(int x) const { return x; } // {\n  const char* s = "{";\n  void g() { if (1) { h("}"); } }\n};\n'
    assert outline.cpp_outline(src) == 'struct A {\n  int f(int x) const; // {\n  const char* s = "{";\n  void g();\n};\n'


@pytest.mark.parametrize("problem", PROBLEMS)
def test_the_instance_outline_keeps_the_fields_and_the_format(problem):
    src = base_pack(problem).make_model_spec().instance_source
    out = outline.py_outline(src)
    assert "def to_text" in out and "def random" not in out and "def parse" not in out and "def save" not in out
    assert len(out) < len(src)
    compile(out, "instance", "exec")


def test_compact_prompts_are_an_option(monkeypatch):
    from llm import native_generator as ng
    from llm import native_mip_generator as nmip
    from llm import native_model_generator as nmg
    from core.packs import oracle_module

    pack = base_pack("clsp")
    ws = Path("generated/clsp_native")
    gen = importlib.import_module(pack.native_module).GENERATION
    existing = ng._existing(ws, "neighborhood")
    spec, cases = pack.make_model_spec(), pack.load_cases()
    oracle = oracle_module(pack)
    names = nmip.oracle_names(oracle)

    def prompts():
        return (ng.generation_prompt(pack, gen, "neighborhood", 3, [], existing, "", ws),
                nmg.model_prompt(spec, cases), nmip.mip_prompt(spec, cases, oracle, names))

    monkeypatch.delenv(outline.ENV, raising=False)
    full = prompts()
    assert (Path(gen["dir"]) / gen["model_header"]).read_text() in full[0] and spec.instance_source in full[1]
    monkeypatch.setenv(outline.ENV, "1")
    compact = prompts()
    assert all(len(c) < len(f) for c, f in zip(compact, full))
    assert "solveFlow(" in compact[0] and spec.instance_source not in compact[1]
    assert nmip.oracle_source(oracle, names) in compact[2]  # el oráculo es la especificación: va completo
