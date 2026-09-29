"""Máquinas de reglas (`core.rules.RuleMachine`): reglas simples y macros con prioridad, con un
controlador fijo. FRG es una regla simple (`bg_move`, 100) y una macro (`reduce_stack`, 50); los
números de cada regla se extraen como parámetros de su clase; el oráculo mide cobertura y
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

from core.rules import RuleMachine


class Fill:
    name = "fill"
    priority = 100

    def allowed(self, L, memory, candidates):
        out = [(L.g(c.sd) - L.g(c.so), c) for c in candidates if L.stacks[c.so] and not L.is_sorted_stack(c.so)
               and L.is_sorted_stack(c.sd) and L.g(c.sd) >= L.g(c.so) and L.g(c.sd) - L.g(c.so) <= 4]
        return [c for _, c in sorted(out, key=lambda t: (t[0], t[1].so, t[1].sd))]


class Unblock:
    name = "unblock"
    priority = 50

    def allowed(self, L, memory, candidates):
        bad = [s for s in range(L.S) if L.stacks[s] and not L.is_sorted_stack(s)]
        if not bad or L.bad() < 3:
            return []
        so = min(bad, key=lambda s: (L.sorted_n[s], s))
        return sorted((c for c in candidates if c.so == so), key=lambda c: (0.5 * L.h(c.sd), c.sd))


def build_component(problem):
    return RuleMachine(problem, [Fill(), Unblock()])
'''


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_frg_is_a_simple_rule_and_a_macro_with_priorities():
    from core.rules import is_macro

    same = 0
    for k in range(10):
        inst = CPMPInstance.cvs_like(5, 5, Random(k))
        P = CPMPModel(inst)
        m = FRGMachine(P)
        assert isinstance(m, RuleMachine) and m.states == ("bg_move", "reduce_stack")
        assert [is_macro(r) for r in m.rules] == [False, True] and [r.priority for r in m.rules] == [100, 50]
        same += GreedyConstructor(P, m).build(inst, Random(0)) == FRGConstructor(P, assignment="never").build(inst, Random(0))
    assert same == 10


def test_numbers_of_each_rule_become_their_own_parameters_and_priority_is_structure(tmp_path):
    from core.validation.params import extract_constants

    src, extracted = extract_constants(RULES_MODULE)
    assert {"fill_allowed_k1", "unblock_allowed_k1", "unblock_allowed_k2"} <= set(extracted)
    assert not any("priority" in k for k in extracted) and "priority = 50" in src
    path = tmp_path / "rules.py"
    path.write_text(src)
    mod = _load(path, "rules_norm")
    P = PACK.make_contexts()[0].problem
    m = mod.build_component(P, fill_allowed_k1=7, unblock_allowed_k1=5)
    fill, unblock = m.rules
    assert fill._auto_fill_allowed_k1 == 7 and unblock._auto_unblock_allowed_k1 == 5
    assert unblock._auto_unblock_allowed_k2 == 0.5  # default
    again, more = extract_constants(src.replace("L.bad() < self._auto_unblock_allowed_k1", "L.bad() < 6"))
    assert list(more) == ["unblock_allowed_k3"] and again.count("def build_component") == 1


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


def test_allowed_actions_match_candidates_by_value_and_bogus_ones_are_rejected():
    """Corrida 71: una regla con su propio `Move = namedtuple(...)` nunca coincidía con el `Move`
    (dataclass) de la vista. Las acciones se comparan por valor; una regla que permite cosas que
    nunca son candidatos se rechaza."""
    from collections import namedtuple

    from core.validation import validate_component
    from examples.cpmp.frg import bg_moves
    from examples.cpmp.machine import BGMove

    NT = namedtuple("Move", ["so", "sd"])

    class NamedBG:
        name = "bg"
        priority = 100

        def allowed(self, L, m, candidates):
            moves = bg_moves(L, False)
            return [NT(so, sd) for so, sd in sorted(moves, key=moves.__getitem__)]

    class Bogus:
        name = "bogus"
        priority = 100

        def allowed(self, L, m, candidates):
            return [NT(99, 98)]

    inst = PACK.make_instances(1, 3, PACK.parse_size("5x5"))[0]
    P = PACK.problem_factory(inst)
    named = P.objective(GreedyConstructor(P, RuleMachine(P, [NamedBG()])).build(inst, Random(0)))
    real = P.objective(GreedyConstructor(P, RuleMachine(P, [BGMove(False)])).build(inst, Random(0)))
    assert named == real  # mismo comportamiento con namedtuple que con la clase de la vista
    c = PACK.make_contexts(strict=False)[0]
    comp = {"name": "b", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "params": {}}
    fb = validate_component(comp, RuleMachine(c.problem, [Bogus()]), c).feedback()
    assert "allowed_are_candidates" in fb or "states_reachable" in fb


def test_an_active_macro_keeps_going_until_done_even_over_higher_priorities():
    """La macro activa sigue aunque una regla de más prioridad aplique; al terminar, decide la
    prioridad."""
    from core.machine import MachinePolicy

    class Any1:
        name = "any"
        priority = 100

        def allowed(self, L, m, candidates):
            return list(candidates) if L.bad() % 2 == 0 else []

    class Drain:  # vacía la pila más alta, de a un contenedor
        name = "drain"
        priority = 50

        def start(self, L, m):
            return max(range(L.S), key=lambda s: (L.h(s), -s))

        def allowed(self, L, m, candidates):
            return [c for c in candidates if c.so == m]

        def done(self, L, m):
            return not L.stacks[m]

    inst = PACK.make_instances(1, 10100, PACK.parse_size("5x5"))[0]
    P = PACK.problem_factory(inst)
    policy = MachinePolicy(RuleMachine(P, [Any1(), Drain()]), P)
    view = P.construction_view(inst)
    policy.bind(view)
    partial, memory, states = view.empty(), None, []
    memory = policy.init(partial)
    for _ in range(40):
        cands = list(view.candidates(partial))
        if view.is_complete(partial) or not cands:
            break
        state, mems = policy.step(partial, memory)
        if states and states[-1][0] == "drain" and not Drain().done(partial, states[-1][1]) and \
                Drain().allowed(partial, states[-1][1], cands):
            assert state == "drain" and mems[1] == states[-1][1]  # sostiene el compromiso
        elif Any1().allowed(partial, None, cands):
            assert state == "any"
        states.append((state, mems[1]))
        a = min(cands, key=lambda c: policy.score(partial, memory, c))
        memory = policy.update(partial, memory, a)
        partial = view.apply(partial, a)
    assert {"any", "drain"} <= {st for st, _ in states}


INIT_MODULE = '''
COMPONENT = {"name": "weighted", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.rules import RuleMachine
from examples.cpmp.construction import Move


class Weighted:
    name = "weighted"
    priority = 100

    def __init__(self, w_gap=8.0, max_bad=1, safe=True):
        self.w_gap = w_gap
        self.max_bad = max_bad
        self.safe = safe

    def allowed(self, L, memory, candidates):
        return sorted(candidates, key=lambda c: (self.w_gap * L.g(c.sd), c.so, c.sd))


def _build_component_llm(problem, **params):
    return RuleMachine(problem, [Weighted()])


def build_component(problem, **params):
    return _build_component_llm(problem, **params)
'''


def test_init_defaults_of_a_rule_are_parameters_even_if_the_module_has_its_own_llm_factory(tmp_path):
    """Corrida 72: los pesos de la regla eran defaults de `__init__` (fuera del tuner) y el módulo ya
    tenía un `_build_component_llm`: renombrar build_component a ese nombre lo volvía recursivo."""
    from core.validation.params import extract_constants

    src, extracted = extract_constants(INIT_MODULE)
    assert {"weighted_w_gap", "weighted_max_bad", "weighted_safe"} <= set(extracted)
    assert extracted["weighted_safe"] == {"type": "bool", "default": True}
    path = tmp_path / "weighted.py"
    path.write_text(src)
    mod = _load(path, "weighted_norm")
    P = PACK.make_contexts()[0].problem
    rule = mod.build_component(P, weighted_w_gap=2.5, weighted_safe=False).rules[0]
    assert (rule.w_gap, rule.max_bad, rule.safe) == (2.5, 1, False)
    assert mod.build_component(P).rules[0].w_gap == 8.0


def test_factory_defaults_passed_args_and_stale_tables_copied_by_the_llm(tmp_path):
    """Corrida 73: (1) `params.get("nombre", 4.0)` en la fábrica es el default de un parámetro, no
    un número suelto; (2) un argumento que la fábrica pasa al construir la regla no se vuelve a
    extraer de su `__init__` (lo pisaría); (3) las tablas `_AUTO` que el LLM copia del padre se
    rehacen desde el código, y el LLM ve el padre sin ellas (`llm_view`)."""
    from core.validation.params import extract_constants, llm_view, loose_constants

    module = INIT_MODULE.replace(
        "return RuleMachine(problem, [Weighted()])",
        "return RuleMachine(problem, [Weighted(w_gap=params.get('w_gap', 4.0))])")
    src, extracted = extract_constants(module)
    assert loose_constants(src) == []
    assert "w_gap" in extracted and "weighted_w_gap" not in extracted and "weighted_max_bad" in extracted
    path = tmp_path / "factory.py"
    path.write_text(src)
    P = PACK.make_contexts()[0].problem
    assert _load(path, "factory_norm").build_component(P, w_gap=1.5).rules[0].w_gap == 1.5

    view = llm_view(src)
    assert "_AUTO" not in view and view.count("def build_component") == 1
    stale = src.replace("_AUTO = {", "_AUTO = {'weighted_gone': 3, ")  # una entrada que el código ya no tiene
    again, more = extract_constants(stale)
    assert "weighted_gone" not in again and more == {}
    back, _ = extract_constants(view)  # el LLM devuelve el padre sin cambios: mismos parámetros
    assert _load_src(tmp_path, back, "back").COMPONENT["params"].keys() == _load_src(tmp_path, src, "orig").COMPONENT["params"].keys()


def _load_src(tmp_path, src, name):
    path = tmp_path / f"{name}.py"
    path.write_text(src)
    return _load(path, name)


def test_numbers_the_factory_gives_a_rule_are_parameters(tmp_path):
    """Corrida 74: `Regla(w_gap=3.0)` dentro de build_component se rechazaba por número suelto."""
    from core.validation.params import extract_constants, loose_constants

    module = INIT_MODULE.replace("return RuleMachine(problem, [Weighted()])",
                                 "return RuleMachine(problem, [Weighted(w_gap=3.0)])")
    src, extracted = extract_constants(module)
    assert loose_constants(src) == [] and extracted["weighted_w_gap"]["default"] == 3.0
    P = PACK.make_contexts()[0].problem
    mod = _load_src(tmp_path, src, "factory_kw")
    assert mod.build_component(P).rules[0].w_gap == 3.0
    assert mod.build_component(P, weighted_w_gap=5.0).rules[0].w_gap == 5.0


def test_unproposed_candidates_are_ranked_by_the_fallback():
    """Si la vista veta todas las propuestas de la regla activa (no volver a un layout visitado),
    desempata el comodín entre los candidatos, no el orden de la vista."""
    from core.machine import FAR, MachinePolicy

    inst = PACK.make_instances(1, 10100, PACK.parse_size("5x5"))[0]
    P = PACK.problem_factory(inst)
    policy = MachinePolicy(FRGMachine(P), P)
    view = P.construction_view(inst)
    policy.bind(view)
    partial = view.empty()
    memory = policy.init(partial)
    state, mems = policy.step(partial, memory)
    proposed = {(a.so, a.sd) for a in policy.machine.allowed(state, partial, mems[policy.machine.index[state]])}
    other = [c for c in view.candidates(partial) if (c.so, c.sd) not in proposed]
    assert other
    for c in other:
        assert policy.score(partial, memory, c) == FAR + policy.fallback.score(partial, c)
