"""La vista MIP escrita por el LLM (`llm.native_mip_generator`): se valida contra el oráculo y los casos, se corrige con
ediciones, no puede importar la vista de referencia, y HYB la usa en lugar de la de referencia."""

from __future__ import annotations

import inspect
from random import Random

import pytest

pytest.importorskip("pulp")

from core.model_parts import MIP_PARTS  # noqa: E402
from examples.lotsizing import model_parts as ref  # noqa: E402
from examples.lotsizing.pack import PACK  # noqa: E402


def _reference_mip_module() -> str:
    """La vista MIP de referencia del CLSP como la escribiría el LLM: importa del oráculo lo que usa."""
    body = "\n\n".join(inspect.getsource(getattr(ref, n)) for n in ("_y",) + MIP_PARTS)
    return f"from __future__ import annotations\n\nfrom examples.lotsizing.model_parts import canonical, _plan\n\n\n{body}"


def _reply(src: str) -> str:
    return f"```python\n{src}\n```"


def test_a_correct_mip_view_is_accepted_and_a_broken_one_is_corrected(tmp_path):
    from llm import ScriptedClient
    from llm.native_mip_generator import generate_mip

    good = _reference_mip_module()
    broken = good.replace('"capacidad": capacity, ', "")
    assert broken != good
    fix = ('<<<<<<< BUSCAR\n    return {"demanda.balance": balance, "enlace": link}\n=======\n'
           '    return {"demanda.balance": balance, "capacidad": capacity, "enlace": link}\n>>>>>>> REEMPLAZAR')
    client = ScriptedClient(responses=[_reply(broken), fix])
    stats = generate_mip(client, PACK, tmp_path, rounds=2, time_limit=10, verbose=False)
    assert stats["accepted"] and stats["rounds"] == 2 and stats["reply_modes"] == ["full", "edits"], stats["rejections"]
    assert (tmp_path / "mip" / "mip.py").read_text() == good
    prompt = client.calls[0][1]
    assert "def _plan(" in prompt and "def constraint_families" in prompt and "def constraint_families(inst: CLSPInstance)" not in prompt


def test_importing_the_reference_mip_view_is_rejected(tmp_path):
    from llm import ScriptedClient
    from llm.native_mip_generator import generate_mip

    cheat = "from examples.lotsizing.model_parts import " + ", ".join(MIP_PARTS) + "\n"
    stats = generate_mip(ScriptedClient(responses=[_reply(cheat)]), PACK, tmp_path, rounds=1, verbose=False)
    assert not stats["accepted"] and "no_forbidden_imports" in stats["rejections"][0]


def test_hyb_uses_the_generated_mip_view(tmp_path):
    from core.packs import load_mip, with_generated_mip

    path = tmp_path / "mip.py"
    path.write_text(_reference_mip_module())
    pack = with_generated_mip(PACK, path)
    inst = PACK.make_instances(1, 3, PACK.parse_size("4x6"))[0]
    P = pack.problem_factory(inst)
    assert P.parts.constraint_families is load_mip(path).constraint_families
    assert P.parts.violations is ref.violations  # el oráculo sigue siendo el de referencia
    destr = next(f for c, f in pack.base_components if c["name"] == "group_window")(P)
    _, free = destr.destroy(ref.trivial_solution(inst), 0.3, Random(0))
    assert free <= set(P.parts.structural_variables(inst))
