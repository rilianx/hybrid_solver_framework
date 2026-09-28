"""Reparación localizada (`llm.patching`): una corrección trae solo las definiciones que cambian y se
reemplazan por nombre en el módulo rechazado; el resto queda idéntico."""

from __future__ import annotations

import ast

import pytest

from llm.patching import PatchError, apply_patch, merge_reply
from tests.test_optimizer import SLOW_SWAP

REQ = ("COMPONENT", "build_component")


def _defs(source: str) -> dict[str, str]:
    """Texto de cada definición (y método) por nombre calificado."""
    out = {}
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef):
                    out[f"{node.name}.{m.name}"] = ast.dump(m)
        elif isinstance(node, (ast.FunctionDef, ast.Assign)):
            out[getattr(node, "name", None) or node.targets[0].id] = ast.dump(node)
    return out


def test_a_patched_method_replaces_only_that_method():
    patch = "class TourSwap:\n    def delta(self, sol, m):\n        return 0.0\n"
    res = apply_patch(SLOW_SWAP, patch, REQ)
    assert res.mode == "patch" and res.replaced == ["TourSwap.delta"] and not res.added
    before, after = _defs(SLOW_SWAP), _defs(res.source)
    assert set(before) == set(after)
    assert [k for k in before if before[k] != after[k]] == ["TourSwap.delta"]
    ns: dict = {}
    exec(res.source, ns)  # noqa: S102
    assert ns["TourSwap"](None).delta((1, 2), (0, 1)) == 0.0


def test_new_helpers_methods_constants_and_imports_are_added():
    patch = ("import math\nfrom examples.cvrp.tour_parts import canonical\n\nSCALE = 2.0\n\n\n"
             "class TourSwap:\n    def __init__(self, problem):\n        self.problem = problem\n        self.k = _k()\n\n"
             "    def size(self):\n        return self.k\n\n\ndef _k():\n    return math.floor(SCALE)\n")
    res = apply_patch(SLOW_SWAP, patch, REQ)
    assert res.replaced == ["TourSwap.__init__"]
    assert res.added == ["import math", "SCALE", "TourSwap.size", "_k"]  # canonical ya estaba importado
    assert res.source.count("from examples.cvrp.tour_parts import canonical") == 1
    ns: dict = {}
    exec(res.source, ns)  # noqa: S102
    assert ns["build_component"](None).size() == 2


def test_a_complete_module_replaces_the_old_one():
    from tests.test_cycle import TOUR_SWAP

    res = apply_patch(SLOW_SWAP, TOUR_SWAP, REQ)
    assert res.mode == "full" and res.source == TOUR_SWAP


def test_a_method_without_its_class_goes_into_the_class():
    """Corridas 43 y 44: la mitad de las correcciones devolvían el método solo, a veces con sangría."""
    for patch in ("def delta(self, sol, m):\n    return 0.0\n", "    def delta(self, sol, m):\n        return 0.0\n"):
        res = apply_patch(SLOW_SWAP, patch, REQ)
        assert res.replaced == ["TourSwap.delta"] and not res.added, res
        ns: dict = {}
        exec(res.source, ns)  # noqa: S102
        assert ns["TourSwap"](None).delta((1, 2), (0, 1)) == 0.0
    res = apply_patch(SLOW_SWAP, "def size(self):\n    return 3\n", REQ)  # método nuevo: a la única clase
    assert res.added == ["TourSwap.size"]


def test_top_level_functions_are_replaced_by_name():
    src = "def a():\n    return 1\n\n\ndef b():\n    return a() + 1\n"
    res = apply_patch(src, "def a():\n    return 10\n", ("a", "b"))
    ns: dict = {}
    exec(res.source, ns)  # noqa: S102
    assert ns["b"]() == 11 and res.replaced == ["a"]


def test_an_unparseable_patch_falls_back_to_the_reply():
    with pytest.raises(PatchError):
        apply_patch(SLOW_SWAP, "def broken(:\n", REQ)
    assert merge_reply(SLOW_SWAP, "def broken(:\n", REQ).mode == "full"
    assert merge_reply(None, "x = 1\n", REQ).source == "x = 1\n"


def test_the_generator_applies_a_correction_patch(tmp_path):
    """Un vecindario que no pasa por un `delta` mal calculado se corrige devolviendo solo `delta`."""
    from llm import ScriptedClient
    from llm.cycle import load_variant
    from llm.generator import generate_slot

    pack = load_variant("cvrp", "tour", None, reference=True)
    wrong = SLOW_SWAP.replace("t0 < 0.0005", "t0 < 0").replace(
        "return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)",
        "return 2 * (self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol))")
    fix = ("class TourSwap:\n    def delta(self, sol, m):\n"
           "        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)\n")
    client = ScriptedClient(responses=[f"```python\n{wrong}\n```", f"```python\n{fix}\n```"])
    accepted, stats = generate_slot(client, pack.make_spec(), "neighborhood", 1, pack.make_contexts(strict=False), tmp_path,
                                    max_rounds=2, verbose=False)
    assert stats.patches == 1 and [c.name for c in accepted] == ["tour_swap"], stats.summary()
    assert "2 * (" not in accepted[0].source and "def moves" in accepted[0].source
