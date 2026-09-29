"""Estrategia `library` de evolve (`llm.library`): el LLM escribe piezas (una regla cada una) y el
compositor las combina en todos los órdenes de prioridad. Con dos piezas angostas escritas a mano
(llenar con BG, sacar el tope de la pila desordenada más baja), el compositor encuentra solo
`bg` > `reduce`, que queda a nivel de FRG."""

from __future__ import annotations

from random import Random

from examples.cpmp.pack import PACK
from llm import ScriptedClient
from llm.evolve import Harness
from llm.library import compose, evolve_library

BG_PIECE = '''
COMPONENT = {"name": "bg_fill", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.rules import RuleMachine
from examples.cpmp.frg import bg_moves


class BGFill:
    """Deja bien puesto un mal puesto sobre una pila ordenada, el menor gasto de grupo primero."""

    name = "bg"

    def allowed(self, L, memory, candidates):
        moves = bg_moves(L, True)
        return sorted((c for c in candidates if (c.so, c.sd) in moves), key=lambda c: (moves[(c.so, c.sd)], c.so, c.sd))


def build_component(problem, **params):
    return RuleMachine(problem, [BGFill()])
'''

REDUCE_PIECE = '''
COMPONENT = {"name": "reduce_lowest", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.rules import RuleMachine
from examples.cpmp.frg import ranked_destinations, select_reduce_stack


class ReduceLowest:
    """Saca el tope de la pila desordenada elegida por FRG hacia los mejores destinos."""

    name = "reduce"

    def allowed(self, L, memory, candidates):
        sr = select_reduce_stack(L, [0] * L.S)
        if sr is None:
            return []
        by = {c.sd: c for c in candidates if c.so == sr}
        return [by[d] for d in ranked_destinations(L, sr) if d in by]


def build_component(problem, **params):
    return RuleMachine(problem, [ReduceLowest()])
'''

WIDE_PIECE = '''
COMPONENT = {"name": "wide", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.rules import RuleMachine


class Wide:
    """Cualquier movimiento, el de destino más alto primero."""

    name = "wide"

    def allowed(self, L, memory, candidates):
        return sorted(candidates, key=lambda c: (-L.g(c.sd), c.so, c.sd))


def build_component(problem, **params):
    return RuleMachine(problem, [Wide()])
'''


def _fenced(src):
    return f"```python\n{src}\n```"


def test_from_two_narrow_pieces_the_composer_finds_bg_over_reduce(tmp_path):
    client = ScriptedClient(responses=[_fenced(BG_PIECE), _fenced(REDUCE_PIECE), _fenced(WIDE_PIECE)])
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=3, tune_samples=1, n_train=3,
                         n_test=3, size="5x5", verbose=False, rng_seed=1)
    rows = [r for r in res.individuals if "round" in r]
    assert [r["op"] for r in rows[:2]] == ["new_rule", "new_rule"]  # sin dos piezas no hay qué combinar
    summary = res.individuals[-1]
    assert summary["best"] == ["bg", "reduce"]  # el orden de FRG, encontrado por el compositor
    assert summary["fitness"] < 0.5 * summary["minimal"]
    first = client.calls[0][1]
    assert "`new_rule`" in first and "ANGOSTA" in first and "(vacía" in first
    second = client.calls[1][1]
    assert "`bg`" in second and "Permite el" in second and "NINGUNA" in second
    assert res.written and "rejected" not in res.written[0], res.written  # la máquina compuesta pasa la validación completa


def test_a_piece_must_be_one_rule_and_new_rules_need_a_new_name(tmp_path):
    two = BG_PIECE.replace("[BGFill()]", "[BGFill(), Other()]").replace("def build_component", '''class Other:
    name = "other"

    def allowed(self, L, memory, candidates):
        return list(candidates)


def build_component''')
    client = ScriptedClient(responses=[_fenced(two), _fenced(two), _fenced(BG_PIECE), _fenced(BG_PIECE), _fenced(BG_PIECE)])
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=2, tune_samples=1, n_train=2,
                         n_test=2, size="4x4", verbose=False)
    rows = [r for r in res.individuals if "round" in r]
    assert rows[0]["status"] == "rechazado" and "UNA regla" in rows[0]["reason"]
    assert rows[1]["status"] != "rechazado"
    client2 = ScriptedClient(responses=[_fenced(BG_PIECE)] * 4)
    res2 = evolve_library(client2, PACK, PACK.make_spec(), tmp_path / "b", Harness(PACK), rounds=2, tune_samples=1,
                          n_train=2, n_test=2, size="4x4", verbose=False)
    rows2 = [r for r in res2.individuals if "round" in r]
    assert rows2[1]["status"] == "rechazado" and "ya hay una pieza" in rows2[1]["reason"]


def test_the_composer_tries_every_order():
    import importlib.util
    import tempfile
    from pathlib import Path

    from llm.library import Piece

    pieces = []
    with tempfile.TemporaryDirectory() as d:
        for i, (name, src) in enumerate([("bg", BG_PIECE), ("reduce", REDUCE_PIECE), ("wide", WIDE_PIECE)]):
            path = Path(d) / f"p{i}.py"
            path.write_text(src)
            spec = importlib.util.spec_from_file_location(f"piece_mod_{i}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            pieces.append(Piece(i, name, name, src, mod.build_component, mod.COMPONENT))
        cache: dict = {}
        ranked = compose(Harness(PACK), pieces, PACK.make_instances(3, 9100, PACK.parse_size("5x5")), cache)
    assert len(cache) == 3 + 6 + 6  # 1, 2 y 3 piezas en todos los órdenes
    assert ranked[0][1][:2] == (0, 1)  # bg sobre reduce
    assert cache[(0, 1)] < cache[(1, 0)] and cache[(0, 1)] < cache[(2,)]


def test_a_piece_is_a_simple_rule_and_the_prompt_has_no_macros_or_priorities(tmp_path):
    """Las piezas son reglas simples: una con `start`/`done` se rechaza, y el prompt no habla de
    macros ni de prioridades (el orden lo decide el compositor)."""
    macro = REDUCE_PIECE.replace("    def allowed(self, L, memory, candidates):", '''    def start(self, L, memory):
        return memory

    def done(self, L, memory):
        return True

    def allowed(self, L, memory, candidates):''')
    client = ScriptedClient(responses=[_fenced(macro), _fenced(macro), _fenced(BG_PIECE)])
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=2, tune_samples=1, n_train=2,
                         n_test=2, size="4x4", verbose=False)
    rows = [r for r in res.individuals if "round" in r]
    assert rows[0]["status"] == "rechazado" and "regla simple" in rows[0]["reason"]
    prompt = client.calls[0][1].lower()
    assert "macro" not in prompt and "prioridad" not in prompt and "priority" not in prompt
