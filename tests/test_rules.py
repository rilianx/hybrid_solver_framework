"""Máquinas de reglas (`core.rules.RuleMachine`): reglas de acción que proponen movimientos y
transiciones que eligen cuál usar. FRG son dos reglas y tres líneas de transiciones; los números
de reglas y transiciones se extraen como parámetros de cada clase; el oráculo mide cobertura y
precisión por regla; `evolve` exige esta estructura."""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from random import Random

import pytest

from core.construction import GreedyConstructor
from core.machine import MachinePolicy
from core.rules import RuleMachine, rule_quality
from examples.cpmp.construction import FRGConstructor
from examples.cpmp.instance import CPMPInstance
from examples.cpmp.machine import FRGMachine
from examples.cpmp.oracle import oracle_distance
from examples.cpmp.pack import PACK
from examples.cpmp.problem_model import CPMPModel

RULES_MODULE = '''
COMPONENT = {"name": "two_rules", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.machine import FALLBACK
from core.rules import RuleMachine
from examples.cpmp.construction import Move


class Fill:
    name = "fill"

    def propose(self, L, memory):
        out = []
        for so in range(L.S):
            if L.stacks[so] and not L.is_sorted_stack(so):
                for sd in range(L.S):
                    if sd != so and L.e(sd) > 0 and L.is_sorted_stack(sd) and L.g(sd) >= L.g(so) and L.g(sd) - L.g(so) <= 4:
                        out.append((L.g(sd) - L.g(so), so, sd))
        return [Move(so, sd) for _, so, sd in sorted(out)]


class Unblock:
    name = "unblock"

    def propose(self, L, memory):
        bad = [s for s in range(L.S) if L.stacks[s] and not L.is_sorted_stack(s)]
        if not bad:
            return []
        so = min(bad, key=lambda s: (L.sorted_n[s], s))
        return [Move(so, sd) for sd in sorted(range(L.S), key=lambda s: (0.5 * L.h(s), s)) if sd != so and L.e(sd) > 0]


class Trans:
    def select(self, L, memory, rules):
        if rules.applies("fill"):
            return "fill", memory
        if L.bad() >= 3 and rules.applies("unblock"):
            return "unblock", memory
        return FALLBACK, memory


def build_component(problem):
    return RuleMachine(problem, [Fill(), Unblock()], Trans())
'''


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frg_is_two_rules_and_three_lines_of_transitions():
    same = 0
    for k in range(10):
        inst = CPMPInstance.cvs_like(5, 5, Random(k))
        P = CPMPModel(inst)
        m = FRGMachine(P)
        assert isinstance(m, RuleMachine) and m.states == ("bg_move", "reduce_stack")
        same += GreedyConstructor(P, m).build(inst, Random(0)) == FRGConstructor(P, assignment="never").build(inst, Random(0))
    assert same == 10


def test_numbers_of_each_rule_and_of_the_transitions_become_their_own_parameters(tmp_path):
    from core.validation.params import extract_constants

    src, extracted = extract_constants(RULES_MODULE)
    assert {"fill_propose_k1", "unblock_propose_k1", "trans_select_k1"} <= set(extracted)
    path = tmp_path / "rules.py"
    path.write_text(src)
    mod = _load(path, "rules_norm")
    P = PACK.make_contexts()[0].problem
    m = mod.build_component(P, fill_propose_k1=7, trans_select_k1=5)
    fill, unblock = m.rules
    assert fill._auto_fill_propose_k1 == 7 and m.transitions._auto_trans_select_k1 == 5
    assert unblock._auto_unblock_propose_k1 == 0.5  # default
    again, more = extract_constants(src.replace("L.bad() >= self._auto_trans_select_k1", "L.bad() >= 6"))
    assert list(more) == ["trans_select_k2"] and again.count("def build_component") == 1


def test_rule_quality_says_how_often_each_rule_applies_and_is_right():
    inst = PACK.make_instances(1, 10100, PACK.parse_size("5x5"))[0]
    P = PACK.problem_factory(inst)
    q = rule_quality(MachinePolicy(FRGMachine(P), P), P.construction_view(inst), lambda p: oracle_distance(inst, p))
    bg, red = q["rules"]["bg_move"], q["rules"]["reduce_stack"]
    assert bg["applies"] > 0 and red["applies"] > 0 and bg["chosen"] + red["chosen"] == q["steps"]
    assert 0 <= bg["optimal"] <= bg["applies"] and bg["optimal"] / bg["applies"] >= 0.5  # el BG casi siempre es óptimo


def test_evolve_asks_for_the_rules_structure(tmp_path):
    from llm.evolve import light_validation
    from tests.test_machine import MACHINE_MODULE  # una máquina de forma libre (estados con score)

    path = tmp_path / "free.py"
    path.write_text(MACHINE_MODULE)
    report, _, _ = light_validation(path, PACK.make_contexts(strict=False))
    assert "rule_machine" in report.feedback()


def test_the_prompt_has_the_quality_of_each_rule(tmp_path):
    from llm.evolve import Harness, Individual, profile, regret_text

    path = tmp_path / "frg_rules.py"
    ind = Individual(0, "frg", "", lambda P, **k: FRGMachine(P, **k), FRGMachine.COMPONENT, ("bg_move", "reduce_stack"))
    profile(Harness(PACK), ind, PACK.make_instances(2, 9100, PACK.parse_size("5x5")))
    text = regret_text(ind)
    assert "Calidad de cada regla" in text and "| bg_move |" in text and "| reduce_stack |" in text


def test_proposals_match_candidates_by_value_and_bogus_proposals_are_rejected():
    """Corrida 71: una regla con su propio `Move = namedtuple(...)` nunca coincidía con el `Move`
    (dataclass) de la vista y la máquina elegía en el orden de la vista. Ahora las acciones se
    comparan por valor; una regla cuyas propuestas no son candidatos se rechaza."""
    from collections import namedtuple

    from core.machine import FALLBACK
    from core.validation import validate_component
    from examples.cpmp.frg import bg_moves

    NT = namedtuple("Move", ["so", "sd"])

    class NamedBG:
        name = "bg"

        def propose(self, L, m):
            moves = bg_moves(L, False)
            return [NT(so, sd) for so, sd in sorted(moves, key=moves.__getitem__)]

    class Bogus:
        name = "bogus"

        def propose(self, L, m):
            return [NT(99, 98)]

    class T:
        def __init__(self, n):
            self.n = n

        def select(self, L, memory, rules):
            return (self.n, memory) if rules.applies(self.n) else (FALLBACK, memory)

    inst = PACK.make_instances(1, 3, PACK.parse_size("5x5"))[0]
    P = PACK.problem_factory(inst)
    named = P.objective(GreedyConstructor(P, RuleMachine(P, [NamedBG()], T("bg"))).build(inst, Random(0)))
    from examples.cpmp.machine import BGMove

    real = P.objective(GreedyConstructor(P, RuleMachine(P, [BGMove(False)], T("bg_move"))).build(inst, Random(0)))
    assert named == real  # mismo comportamiento con namedtuple que con la clase de la vista
    c = PACK.make_contexts(strict=False)[0]
    comp = {"name": "b", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "params": {}}
    assert "proposals_are_candidates" in validate_component(comp, RuleMachine(c.problem, [Bogus()], T("bogus")), c).feedback()
