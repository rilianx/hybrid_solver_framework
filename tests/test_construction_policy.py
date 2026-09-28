"""Slot `construction_policy`: un puntaje con memoria. El greedy y la beam search llevan la
memoria junto al parcial; la validación exige memorias hashables y deterministas y que ni
`score` ni `update` modifiquen nada; entra al catálogo como `greedy_<nombre>` / `beam_<nombre>`
y se genera con el LLM como cualquier otro slot."""

from __future__ import annotations

import importlib.util
import textwrap
from dataclasses import replace
from pathlib import Path
from random import Random

import pytest

from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor, as_policy, is_policy
from core.validation import validate_component
from examples.cpmp.construction import DestinationRank, FRGConstructor, FRGPolicy
from examples.cpmp.instance import CPMPInstance
from examples.cpmp.problem_model import CPMPModel

COMP = {"name": "p", "slot": "construction_policy", "compatible_skeletons": ["CONSTRUCT"], "params": {}}

PLAN = textwrap.dedent('''
    COMPONENT = {"name": "empty_target_then_fill", "slot": "construction_policy", "compatible_skeletons": ["CONSTRUCT"],
                 "requires": [], "params": {}}


    class EmptyTargetThenFill:
        """Si un movimiento deja bien puesto un mal puesto, hacerlo; si no, vaciar la pila
        desordenada más baja (la memoria recuerda cuál) hasta que quede vacía u ordenada."""

        def __init__(self, problem):
            self.problem = problem

        def init(self, partial):
            return (None,)

        def _target(self, partial, memory):
            t = memory[0]
            if t is not None and partial.stacks[t] and not partial.is_sorted_stack(t):
                return t
            cands = [s for s in range(partial.S) if partial.stacks[s] and not partial.is_sorted_stack(s)]
            return min(cands, key=lambda s: (partial.h(s), s)) if cands else None

        def score(self, partial, memory, action):
            so, sd = action.so, action.sd
            c = partial.g(so)
            if not partial.is_sorted_stack(so) and partial.is_sorted_stack(sd) and partial.g(sd) >= c:
                return float(partial.g(sd) - c)
            t = self._target(partial, memory)
            if so != t:
                return 1e6 + partial.h(so)
            if sd == t:
                return 1e7
            blocks = 0 if partial.g(sd) >= c else 1
            return 1e3 + 100.0 * blocks + partial.h(sd)

        def update(self, partial, memory, action):
            t = self._target(partial, memory)
            return (t,) if action.so == t else memory


    def build_component(problem, **params):
        return EmptyTargetThenFill(problem)
''')


def _module(tmp_path: Path, src: str, name: str = "plan"):
    path = tmp_path / f"{name}.py"
    path.write_text(src)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def contexts():
    from examples.cpmp.pack import PACK

    # umbral de calidad laxo: estos tests ejercitan el contrato, no la calidad
    return [replace(c, constructor_max_relative_gap=50.0, diversity_probe=None) for c in PACK.make_contexts()]


def test_a_stateless_score_is_a_policy_without_memory():
    P = CPMPModel(CPMPInstance.cvs_like(4, 5, Random(0)))
    score = DestinationRank(P)
    assert not is_policy(score) and is_policy(FRGPolicy(P))
    pol = as_policy(score)
    L = P.construction_view(P.inst).empty()
    assert pol.init(L) is None and pol.update(L, None, None) is None


def test_the_greedy_carries_the_memory(tmp_path):
    """Con memoria, el greedy de FRG como política reproduce FRG; la política de vaciar una pila
    se aparta del miope (sostiene el plan)."""
    same = 0
    for k in range(5):
        inst = CPMPInstance.cvs_like(5, 6, Random(k))
        P = CPMPModel(inst)
        a = GreedyConstructor(P, FRGPolicy(P)).build(inst, Random(0))
        b = FRGConstructor(P, assignment="never").build(inst, Random(0))
        assert P.is_feasible(a)
        same += a == b
    assert same >= 4
    plan = _module(tmp_path, PLAN)
    inst = CPMPInstance.cvs_like(5, 5, Random(1000))
    P = CPMPModel(inst)
    with_plan = P.objective(GreedyConstructor(P, plan.build_component(P)).build(inst, Random(0)))
    myopic = P.objective(GreedyConstructor(P, DestinationRank(P)).build(inst, Random(0)))
    assert with_plan < myopic


def test_the_beam_search_carries_one_memory_per_node(tmp_path):
    plan = _module(tmp_path, PLAN)
    for k in range(3):
        inst = CPMPInstance.cvs_like(5, 5, Random(1000 + k))
        P = CPMPModel(inst)
        policy = plan.build_component(P)
        g = P.objective(GreedyConstructor(P, policy).build(inst, Random(0)))
        b = BeamSearchConstructor(P, policy, beam_width=3, branching=6)
        sol = b.build(inst, Random(0))
        assert P.is_feasible(sol) and P.objective(sol) <= g
        # el puntaje que ordena y el rollout pueden ser distintos: cada uno con su memoria
        mixed = BeamSearchConstructor(P, DestinationRank(P), rollout=policy, beam_width=3, branching=6).build(inst, Random(0))
        assert P.is_feasible(mixed)


def test_validation_accepts_policies_and_rejects_broken_ones(contexts, tmp_path):
    for c in contexts:
        assert validate_component(dict(COMP, name="frg_policy"), FRGPolicy(c.problem), c).passed
        plan = _module(tmp_path, PLAN).build_component(c.problem)
        r = validate_component(dict(COMP, name="plan"), plan, c)
        assert r.passed, r.feedback()

    class ListMemory:  # memoria no hashable
        def init(self, p): return []
        def score(self, p, m, a): return 0.0
        def update(self, p, m, a): return m + [a]

    class MutatesMemory:
        def init(self, p): return {"n": 0}
        def score(self, p, m, a): m["n"] = m.get("n", 0) + 1; return 0.0
        def update(self, p, m, a): return m

    class Random_:
        def __init__(self): self.rng = Random(0)
        def init(self, p): return ()
        def score(self, p, m, a): return self.rng.random()
        def update(self, p, m, a): return ()

    c = contexts[0]
    assert "memory_hashable" in validate_component(dict(COMP, name="a"), ListMemory(), c).feedback()
    assert not validate_component(dict(COMP, name="b"), MutatesMemory(), c).passed
    assert "deterministic" in validate_component(dict(COMP, name="c"), Random_(), c).feedback()


def test_policies_enter_the_catalog_as_greedy_and_beam():
    from examples.cpmp.catalog import build_registry

    names = {s.name for s in build_registry().for_slot("constructor")}
    assert {"greedy_frg_policy", "beam_frg_policy"} <= names
    assert [s.name for s in build_registry().for_slot("construction_policy")] == ["frg_policy"]


def test_prompt_and_generation_of_a_policy(contexts, tmp_path):
    from examples.cpmp.pack import PACK
    from llm import ScriptedClient, generate_slot
    from llm.prompts import generation_prompt

    p = generation_prompt(PACK.make_spec(), "construction_policy", 2)
    assert "class ConstructionPolicy(Protocol)" in p and "fill_then_top_up" in p and "class Layout" in p
    broken = PLAN.replace("return (t,) if action.so == t else memory", "return [t]")  # memoria no hashable
    client = ScriptedClient(responses=[f"```python\n{broken}\n```", f"```python\n{PLAN}\n```"])
    accepted, stats = generate_slot(client, PACK.make_spec(), "construction_policy", 1, contexts[:1], tmp_path,
                                    max_rounds=2, verbose=False)
    assert [c.name for c in accepted] == ["empty_target_then_fill"], stats.rejections_by_layer
    assert stats.rounds_per_accepted == {"empty_target_then_fill": 2}
    assert "memory_hashable" in client.calls[1][1]


def test_the_optimizer_measures_constructive_work_on_a_model_without_mip():
    """Sin vista MIP, la velocidad que se optimiza es la del trabajo constructivo (trivial_solution,
    construcciones y evaluaciones), y el perfil dice dónde está el tiempo."""
    from core.validation.equivalence import model_speed, parts_profile
    from examples.cpmp import model_parts as ref
    from examples.cvrp import model_parts as cvrp_ref

    inst = CPMPInstance.cvs_like(4, 4, Random(3))
    speed, unit = model_speed(ref, inst)
    assert unit == "unidades de trabajo constructivo/s" and speed > 0
    prof = parts_profile(ref, inst)
    assert set(prof) == {"trivial_solution (s)", "una construcción al azar, con complete_partial si hace falta (s)",
                         "200 evaluaciones violations + cost_terms (s)"}
    from examples.cvrp.instance import CVRPInstance

    assert model_speed(cvrp_ref, CVRPInstance.random(6, Random(0)))[1] == "evaluaciones/s"  # con vista MIP, como antes


def test_the_penalty_of_a_parts_model_is_computed_once_per_instance():
    from core.model_parts import PartsModel
    from examples.cpmp import model_parts as ref

    calls = {"n": 0}

    class Counting:
        def __getattr__(self, name):
            return getattr(ref, name)

        def trivial_solution(self, inst):
            calls["n"] += 1
            return ref.trivial_solution(inst)

    parts, inst = Counting(), CPMPInstance.cvs_like(4, 4, Random(5))
    PartsModel(parts, inst)
    PartsModel(parts, inst)
    assert calls["n"] == 1
