"""Etapa `improve` (`llm.improver`): desde una base (generada o una semilla a mano), con
diagnósticos, el LLM propone una variante; se acepta solo si valida y gana a la base en
instancias apartadas, y pasa a ser la nueva base."""

from __future__ import annotations

import json

from examples.cpmp.catalog import build_registry
from examples.cpmp.pack import PACK
from llm import ScriptedClient
from llm.improver import Harness, base_from_handwritten, base_from_workspace, compare, improve_component
from tests.test_phases import PHASE_MODULE

BETTER = '''
COMPONENT = {"name": "unblock_lowest_v1", "slot": "phase", "compatible_skeletons": ["CONSTRUCT"], "requires": [], "params": {}}

from examples.cpmp.phases import ReduceStack


def build_component(problem):
    return ReduceStack(problem)
'''

INERT = '''
COMPONENT = {"name": "unblock_lowest_v1", "slot": "phase", "compatible_skeletons": ["CONSTRUCT"], "requires": [], "params": {}}


class Inert:
    def init(self, partial):
        return ()

    def score(self, partial, memory, action):
        return 0.0

    def update(self, partial, memory, action):
        return memory


def build_component(problem):
    return Inert()
'''


def _workspace(tmp_path):
    (tmp_path / "phase").mkdir()
    (tmp_path / "phase" / "unblock_lowest_r1.py").write_text(PHASE_MODULE)
    return tmp_path


def test_a_better_variant_replaces_the_base_and_a_bad_one_is_explained(tmp_path):
    ws = _workspace(tmp_path)
    base = base_from_workspace(ws, "phase", "unblock_lowest")
    harness = Harness(PACK, build_registry(), "phase", context=["bg_fill", "*"])
    client = ScriptedClient(responses=[f"```python\n{INERT}\n```", f"```python\n{BETTER}\n```"])
    res = improve_component(client, PACK, harness.registry, PACK.make_spec(), base, ws, harness, rounds=2, n_train=2, n_test=4,
                            verbose=False)
    assert [a["name"] for a in res.accepted] == ["unblock_lowest_v1"] and res.final == "unblock_lowest_v1"
    assert res.accepted[0]["after"] < res.accepted[0]["before"]
    assert (ws / "phase" / "unblock_lowest_v1_r1.py").exists()
    first, second = client.calls[0][1], client.calls[1][1]
    assert "class UnblockLowest" in first and "cota inferior" in first and "unblock_lowest:" in first  # base, diagnósticos, traza
    assert "Intentos anteriores rechazados" in second and "adds_value" in second


def test_a_variant_that_does_not_win_on_held_out_instances_is_rejected(tmp_path):
    """Desde la semilla a mano (la reducción de FRG, en la combinación [bg_fill, *]), una variante
    que construye lo mismo valida pero no gana: se rechaza y no queda en el workspace."""
    base = base_from_handwritten(PACK, "phase", "reduce_stack")
    harness = Harness(PACK, build_registry(), "phase", context=["bg_fill", "*"])
    same = BETTER.replace("unblock_lowest_v1", "reduce_stack_v1")
    client = ScriptedClient(responses=[f"```python\n{same}\n```"])
    res = improve_component(client, PACK, harness.registry, PACK.make_spec(), base, tmp_path, harness, rounds=1, n_train=2,
                            n_test=4, verbose=False)
    assert res.seed and not res.accepted and "no gana a la base" in res.rejections[0], res.rejections
    assert not (tmp_path / "phase" / "reduce_stack_v1_r1.py").exists()
    assert "heurística publicada" in client.calls[0][1]


def test_a_handwritten_seed_is_a_self_contained_module():
    base = base_from_handwritten(PACK, "phase", "reduce_stack")
    assert base.seed and "class ReduceStack" in base.source
    assert "from examples.cpmp.frg import" in base.source and "from .frg" not in base.source


def test_compare_needs_a_lower_mean_and_more_wins():
    assert compare([10, 10, 10], [9, 9, 11])[0]
    assert not compare([10, 10, 10], [5, 11, 11])[0]  # media menor pero pierde en más
    assert not compare([10, 10], [9, float("inf")])[0]  # falla donde la base no
