"""Etapa `improve` (`llm.improver`): desde una base (generada o una semilla a mano), con
diagnósticos, el LLM propone una variante; se acepta solo si valida y gana a la base en
instancias apartadas, y pasa a ser la nueva base."""

from __future__ import annotations

import json

from examples.cpmp.catalog import build_registry
from examples.cpmp.pack import PACK
from llm import ScriptedClient
from llm.improver import Harness, base_from_handwritten, base_from_workspace, compare, improve_component
from tests.test_machine import MACHINE_MODULE

BETTER = '''
COMPONENT = {"name": "fill_then_unblock_v1", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"],
             "requires": [], "params": {}}

from examples.cpmp.machine import FRGMachine


def build_component(problem):
    return FRGMachine(problem)
'''

INERT = '''
COMPONENT = {"name": "fill_then_unblock_v1", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"],
             "requires": [], "params": {}}


class Inert:
    states = ("only",)

    def initial(self, partial):
        return "only", ()

    def transition(self, partial, state, memory):
        return state, memory

    def score(self, partial, state, memory, action):
        return 0.0

    def update(self, partial, state, memory, action):
        return memory


def build_component(problem):
    return Inert()
'''


def _workspace(tmp_path):
    (tmp_path / "construction_machine").mkdir()
    (tmp_path / "construction_machine" / "fill_then_unblock_r1.py").write_text(MACHINE_MODULE)
    return tmp_path


def test_a_better_variant_replaces_the_base_and_a_bad_one_is_explained(tmp_path):
    ws = _workspace(tmp_path)
    base = base_from_workspace(ws, "construction_machine", "fill_then_unblock")
    harness = Harness(PACK, build_registry(), "construction_machine")
    client = ScriptedClient(responses=[f"```python\n{INERT}\n```", f"```python\n{BETTER}\n```"])
    res = improve_component(client, PACK, harness.registry, PACK.make_spec(), base, ws, harness, rounds=2, n_train=2, n_test=4,
                            verbose=False)
    assert [a["name"] for a in res.accepted] == ["fill_then_unblock_v1"] and res.final == "fill_then_unblock_v1"
    assert res.accepted[0]["after"] < res.accepted[0]["before"]
    assert (ws / "construction_machine" / "fill_then_unblock_v1_r1.py").exists()
    first, second = client.calls[0][1], client.calls[1][1]
    assert "class FillThenUnblock" in first and "cota inferior" in first and "unblock:" in first  # base, diagnósticos, traza por estado
    assert "Intentos anteriores rechazados" in second


def test_a_variant_that_does_not_win_on_held_out_instances_is_rejected(tmp_path):
    """Desde la semilla a mano (FRG como máquina), una variante que construye lo mismo valida pero
    no gana: se rechaza y no queda en el workspace."""
    base = base_from_handwritten(PACK, "construction_machine", "frg_machine")
    harness = Harness(PACK, build_registry(), "construction_machine")
    same = BETTER.replace("fill_then_unblock_v1", "frg_machine_v1")
    client = ScriptedClient(responses=[f"```python\n{same}\n```"])
    res = improve_component(client, PACK, harness.registry, PACK.make_spec(), base, tmp_path, harness, rounds=1, n_train=2,
                            n_test=4, verbose=False)
    assert res.seed and not res.accepted and "no gana a la base" in res.rejections[0], res.rejections
    assert not (tmp_path / "construction_machine" / "frg_machine_v1_r1.py").exists()
    assert "heurística publicada" in client.calls[0][1]


def test_a_handwritten_seed_is_a_self_contained_module():
    base = base_from_handwritten(PACK, "construction_machine", "frg_machine")
    assert base.seed and "class FRGMachine" in base.source
    assert "from examples.cpmp.frg import" in base.source and "from .frg" not in base.source


def test_compare_needs_a_lower_mean_and_more_wins():
    assert compare([10, 10, 10], [9, 9, 11])[0]
    assert not compare([10, 10, 10], [5, 11, 11])[0]  # media menor pero pierde en más
    assert not compare([10, 10], [9, float("inf")])[0]  # falla donde la base no
