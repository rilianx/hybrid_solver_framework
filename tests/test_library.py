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
                         n_test=3, size="5x5", verbose=False, parts=False, rng_seed=1)
    rows = [r for r in res.individuals if "round" in r]
    assert [r["op"] for r in rows[:2]] == ["new_rule", "new_rule"]  # sin dos piezas no hay qué combinar
    summary = res.individuals[-1]
    assert summary["best"] == ["bg", "reduce"]  # el orden de FRG, encontrado por el compositor
    assert summary["fitness"] < 0.5 * summary["minimal"]
    first = client.calls[0][1]
    assert "`new_rule`" in first and "ANGOSTA" in first and "(vacía" in first
    second = client.calls[1][1]
    assert "`bg`" in second and "Permite el" in second and "NINGUNA" in second
    assert "rollout" in second and "óptimo" not in second  # sin oráculo: se compara solo por rollout
    assert res.written and "rejected" not in res.written[0], res.written  # la máquina compuesta pasa la validación completa


def test_a_piece_must_be_one_rule_and_new_rules_need_a_new_name(tmp_path):
    two = BG_PIECE.replace("[BGFill()]", "[BGFill(), Other()]").replace("def build_component", '''class Other:
    name = "other"

    def allowed(self, L, memory, candidates):
        return list(candidates)


def build_component''')
    client = ScriptedClient(responses=[_fenced(two), _fenced(two), _fenced(BG_PIECE), _fenced(BG_PIECE), _fenced(BG_PIECE)])
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=2, tune_samples=1, n_train=2,
                         n_test=2, size="4x4", verbose=False, parts=False)
    rows = [r for r in res.individuals if "round" in r]
    assert rows[0]["status"] == "rechazado" and "UNA regla" in rows[0]["reason"]
    assert rows[1]["status"] != "rechazado"
    client2 = ScriptedClient(responses=[_fenced(BG_PIECE)] * 4)
    res2 = evolve_library(client2, PACK, PACK.make_spec(), tmp_path / "b", Harness(PACK), rounds=2, tune_samples=1,
                          n_train=2, n_test=2, size="4x4", verbose=False, parts=False)
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
                         n_test=2, size="4x4", verbose=False, parts=False)
    rows = [r for r in res.individuals if "round" in r]
    assert rows[0]["status"] == "rechazado" and "regla simple" in rows[0]["reason"]
    prompt = client.calls[0][1].lower()
    assert "macro" not in prompt and "prioridad" not in prompt and "priority" not in prompt


def test_resume_reuses_the_evaluated_compositions_and_the_best(tmp_path):
    """Corrida 83: al retomar se recalculaba la biblioteca entera y el job se agotaba en 3 rondas.
    Ahora se guardan las composiciones evaluadas y la mejor, y se reusan con las mismas instancias."""
    import json

    client = ScriptedClient(responses=[_fenced(BG_PIECE), _fenced(REDUCE_PIECE)])
    first = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=2, tune_samples=1, n_train=2,
                           n_test=2, size="5x5", verbose=False, parts=False)
    saved = json.loads((tmp_path / "evolve_library.json").read_text())
    assert saved["cache"] and saved["state"]["best"] and saved["key"] == "5x5|2"

    calls = []

    class Counting(Harness):
        def mean(self, *a, **k):
            calls.append(1)
            return super().mean(*a, **k)

    again = evolve_library(ScriptedClient(responses=[]), PACK, PACK.make_spec(), tmp_path, Counting(PACK), rounds=0,
                           tune_samples=1, n_train=2, n_test=2, size="5x5", verbose=False, parts=False, resume=True)
    assert again.individuals[-1]["best"] == first.individuals[-1]["best"] == ["bg", "reduce"]
    assert len(calls) <= 3  # el comodín solo y la salida; nada de recomponer


def test_the_llm_chooses_the_action_and_sees_the_history(tmp_path):
    """Con `choose="llm"` el LLM decide si escribe una pieza nueva o mejora cuál (líneas ACCIÓN / POR QUÉ)."""
    refined = BG_PIECE.replace('"name": "bg_fill"', '"name": "bg_fill_v2"').replace(
        "key=lambda c: (moves[(c.so, c.sd)], c.so, c.sd)", "key=lambda c: (moves[(c.so, c.sd)], -c.so, c.sd)")
    answer = "ACCIÓN: mejorar bg\nPOR QUÉ: desempatar por la pila de origen más alta\n" + _fenced(refined)
    client = ScriptedClient(responses=[_fenced(BG_PIECE), _fenced(REDUCE_PIECE), answer, _fenced(WIDE_PIECE)])
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=4, tune_samples=1, n_train=2,
                         n_test=2, size="5x5", verbose=False, parts=False)
    rows = [r for r in res.individuals if "round" in r]
    assert rows[2]["op"] == "refine_rule" and rows[2]["target"] == "bg" and "desempatar" in rows[2]["why"]
    third, fourth = client.calls[2][1], client.calls[3][1]
    assert "ACCIÓN: nueva" in third and "por paso" in third and "# Pieza `bg`" in third
    assert "# Rondas anteriores" in fourth and "mejorar `bg`" in fourth


def test_rollout_evidence_covers_instances_beyond_the_oracle():
    """Corrida 85: el oráculo solo alcanza 5×5 y ahí la máquina es casi óptima; la pérdida estaba en 6×6.
    Por rollout (cada acción completada con la misma máquina) se ven los pasos donde otra acción termina mejor,
    en cualquier tamaño y también con el comodín solo."""
    import importlib.util
    import tempfile
    from pathlib import Path

    from llm.library import Piece, rollout_evidence

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "bg.py"
        path.write_text(BG_PIECE)
        spec = importlib.util.spec_from_file_location("bg_roll", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        bg = Piece(0, "bg", "bg", BG_PIECE, mod.build_component, mod.COMPONENT)
        big = PACK.make_instances(1, 9150, PACK.parse_size("6x6"))
        text, regret, steps = rollout_evidence(Harness(PACK), (bg,), [bg], big)
    assert "rollout" in text and "terminaría en" in text and regret
    with tempfile.TemporaryDirectory():
        text, regret, steps = rollout_evidence(Harness(PACK), (), [bg], PACK.make_instances(1, 9100, PACK.parse_size("5x5")))
    assert "decidió el comodín" in text and steps


def test_a_new_piece_is_also_tried_inserted_into_the_best_machine():
    """Corrida 86: la mejor máquina ya usaba 3 piezas (el máximo), así que una pieza nueva solo podía
    reemplazar a otra. Ahora también se prueba insertada en cada posición de la mejor."""
    import importlib.util
    import tempfile
    from pathlib import Path

    from llm.library import Piece

    pieces = []
    with tempfile.TemporaryDirectory() as d:
        for i, (name, src) in enumerate([("bg", BG_PIECE), ("reduce", REDUCE_PIECE), ("wide", WIDE_PIECE)]):
            path = Path(d) / f"q{i}.py"
            path.write_text(src)
            spec = importlib.util.spec_from_file_location(f"piece_ins_{i}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            pieces.append(Piece(i, name, name, src, mod.build_component, mod.COMPONENT))
        pieces[2].width = 1.0  # ancha: solo al final
        import llm.library as L

        old = L.MAX_PIECES
        L.MAX_PIECES = 1
        try:
            cache: dict = {}
            compose(Harness(PACK), pieces, PACK.make_instances(2, 9100, PACK.parse_size("5x5")), cache, must=pieces[1],
                    best=(0, 2))
        finally:
            L.MAX_PIECES = old
    assert {(1, 0, 2), (0, 1, 2)} <= set(cache)  # insertada antes de la pieza ancha, que queda al final
    assert (0, 2, 1) not in cache  # la ancha solo va al final


# --- orígenes y colocación (core.parts) --------------------------------------------------
BG_ORIGIN = '''
COMPONENT = {"name": "bg_origin", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.parts import origin_machine


class BGOrigin:
    """Pilas desordenadas cuyo tope puede quedar bien puesto sobre una ordenada, la de menor gasto de grupo primero."""

    name = "bg"

    def sources(self, L, memory):
        out = []
        for so in range(L.S):
            if not L.stacks[so] or L.is_sorted_stack(so):
                continue
            c = L.g(so)
            gaps = [L.g(sd) - c for sd in range(L.S)
                    if sd != so and L.e(sd) > 0 and L.is_sorted_stack(sd) and L.g(sd) >= c]
            if gaps:
                out.append((min(gaps), so))
        return [so for _, so in sorted(out)]


def build_component(problem, **params):
    return origin_machine(problem, BGOrigin())
'''

REDUCE_ORIGIN = '''
COMPONENT = {"name": "reduce_origin", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.parts import origin_machine
from examples.cpmp.frg import select_reduce_stack


class ReduceOrigin:
    """La pila que elige FRG para reducir."""

    name = "reduce"

    def sources(self, L, memory):
        sr = select_reduce_stack(L, [0] * L.S)
        return [] if sr is None else [sr]


def build_component(problem, **params):
    return origin_machine(problem, ReduceOrigin())
'''

FRG_PLACE = '''
COMPONENT = {"name": "frg_place", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.parts import placement_machine
from examples.cpmp.frg import destination_rank


class FRGPlace:
    """Donde quede bien puesto y más ajustado; si no, donde menos estorbe."""

    name = "frg_place"

    def rank(self, L, action):
        return destination_rank(L, L.g(action.so), action.sd)


def build_component(problem, **params):
    return placement_machine(problem, FRGPlace())
'''


def test_frg_is_two_origins_and_one_placement():
    """FRG separado en qué se mueve y adónde: `bg` > `reduce` como orígenes con la colocación de FRG queda a
    nivel de FRG; con la colocación por defecto (la cota) ya baja de 83 a ~21; al revés no sirve."""
    import importlib.util
    import tempfile
    from pathlib import Path

    from core.parts import assemble, kind_of

    mods = {}
    with tempfile.TemporaryDirectory() as d:
        for name, src in (("bg", BG_ORIGIN), ("reduce", REDUCE_ORIGIN), ("place", FRG_PLACE)):
            path = Path(d) / f"part_{name}.py"
            path.write_text(src)
            spec = importlib.util.spec_from_file_location(f"part_{name}", path)
            mods[name] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mods[name])
    P0 = PACK.make_contexts(strict=False)[0].problem
    assert [kind_of(mods[n].build_component(P0)) for n in ("bg", "reduce", "place")] == ["origin", "origin", "place"]
    test = PACK.make_instances(4, 10100, PACK.parse_size("5x5"))
    H = Harness(PACK)

    def machine(*names):
        return lambda P, **_: assemble(P, [mods[n].build_component(P) for n in names], [100, 50, 25])

    frg_like = H.mean(machine("place", "bg", "reduce"), {}, test)
    default = H.mean(machine("bg", "reduce"), {}, test)
    backwards = H.mean(machine("place", "reduce", "bg"), {}, test)
    assert frg_like < 14 and default < 16 and backwards > 2 * frg_like, (frg_like, default, backwards)


def test_with_parts_the_composer_finds_bg_reduce_and_the_placement(tmp_path):
    client = ScriptedClient(responses=[_fenced(BG_ORIGIN), _fenced(REDUCE_ORIGIN),
                                       "ACCIÓN: colocación nueva\nPOR QUÉ: hay contraejemplos con el mismo origen\n"
                                       + _fenced(FRG_PLACE)])
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=3, tune_samples=1, n_train=3,
                         n_test=3, size="5x5", verbose=False, rng_seed=1)
    rows = [r for r in res.individuals if "round" in r]
    assert [r["op"] for r in rows] == ["new_origin", "new_origin", "new_place"], rows
    assert [r["kind"] for r in rows] == ["origin", "origin", "place"]
    summary = res.individuals[-1]
    assert summary["best"] == ["frg_place", "bg", "reduce"], summary["best"]
    first, third = client.calls[0][1], client.calls[2][1]
    assert "ORIGEN" in first and "origin_machine" in first and "la pila de la que sale" in first
    assert "colocación nueva" in third and "placement_machine" in third and "colocación (por defecto)" in third
    assert res.written and "rejected" not in res.written[0], res.written


def test_with_parts_a_piece_must_be_the_kind_asked_for(tmp_path):
    client = ScriptedClient(responses=[_fenced(BG_PIECE), _fenced(BG_PIECE)])  # un movimiento completo, no un origen
    res = evolve_library(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=1, n_train=2,
                         n_test=2, size="4x4", verbose=False)
    row = [r for r in res.individuals if "round" in r][0]
    assert row["status"] == "rechazado" and "ORIGEN" in row["reason"] and "origin_machine" in row["reason"]
