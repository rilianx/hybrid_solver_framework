"""Construcción por fases (slot `phase`, `core.phases.PhasedPolicy`): FRG se expresa como dos fases
chicas; una fase se valida por lo que aporta con el comodín nulo; la cantidad de fases es un
parámetro del tuner (`greedy_phased` / `beam_phased`, `n_phases` y `phase_j` condicionales)."""

from __future__ import annotations

from dataclasses import replace
from random import Random

import pytest

from config_space import suggest_from_space
from core.assembler import ALL_SKELETONS, Assembler
from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor
from core.phases import NullPhase, PhasedPolicy, alone, phase_trace
from core.validation import validate_component
from examples.cpmp.construction import FRGConstructor
from examples.cpmp.instance import CPMPInstance
from examples.cpmp.phases import BGFill, ReduceStack
from examples.cpmp.problem_model import CPMPModel
from examples.lotsizing.random_search import RandomTrial


def _frg_phases(P):
    return PhasedPolicy([BGFill(P), ReduceStack(P)], names=["bg_fill", "reduce_stack"])


@pytest.fixture(scope="module")
def contexts():
    from examples.cpmp.pack import PACK

    return [replace(c, diversity_probe=None) for c in PACK.make_contexts()]


def test_two_phases_are_frg():
    """El greedy con [llenar, reducir] hace los mismos movimientos que FRG sin asignación."""
    same = 0
    for k in range(10):
        inst = CPMPInstance.cvs_like(5, 5, Random(k))
        P = CPMPModel(inst)
        same += GreedyConstructor(P, _frg_phases(P)).build(inst, Random(0)) == FRGConstructor(P, assignment="never").build(inst, Random(0))
    assert same == 10


def test_the_active_phase_holds_control_until_done():
    """Llenar se vuelve a elegir en cada paso; una reducción sigue hasta su criterio de parada, y
    mientras tanto llenar no toma el control aunque haya un BG."""
    inst = CPMPInstance.cvs_like(5, 5, Random(3))
    P = CPMPModel(inst)
    trace = phase_trace(_frg_phases(P), P.construction_view(inst))
    names = [n for n, _ in trace]
    assert {"bg_fill", "reduce_stack"} <= set(names)
    runs = [a.so for n, a in trace if n == "reduce_stack"]
    assert runs and len(set(runs)) < len(runs)  # la misma pila se reduce en varios pasos seguidos


def test_the_order_and_count_of_phases_matter():
    inst = CPMPInstance.cvs_like(5, 5, Random(1))
    P = CPMPModel(inst)
    frg = P.objective(GreedyConstructor(P, _frg_phases(P)).build(inst, Random(0)))
    only_reduce = P.objective(GreedyConstructor(P, PhasedPolicy([ReduceStack(P)])).build(inst, Random(0)))
    null = P.objective(GreedyConstructor(P, PhasedPolicy([NullPhase()])).build(inst, Random(0)))
    assert frg < only_reduce and frg < null


def test_a_phase_is_validated_by_what_it_adds(contexts):
    for c in contexts:
        for name, phase in (("bg_fill", BGFill(c.problem)), ("reduce_stack", ReduceStack(c.problem))):
            comp = {"name": name, "slot": "phase", "compatible_skeletons": ["CONSTRUCT"], "params": {}}
            r = validate_component(comp, phase, c)
            assert r.passed, r.feedback()

    class Never:  # nunca toma el control
        def init(self, p): return ()
        def applies(self, p, m): return False
        def score(self, p, m, a): return 0.0
        def update(self, p, m, a): return m

    comp = {"name": "never", "slot": "phase", "compatible_skeletons": ["CONSTRUCT"], "params": {}}
    assert "takes_control" in validate_component(comp, Never(), contexts[0]).feedback()
    comp = dict(comp, name="null")
    assert "adds_value" in validate_component(comp, NullPhase(), contexts[0]).feedback()


def test_the_number_of_phases_is_a_tuner_parameter():
    from examples.cpmp.catalog import build_registry
    from examples.cpmp.pack import PACK

    reg = build_registry()
    asm = Assembler(problem_factory=PACK.problem_factory, registry=reg, skeletons={"CONSTRUCT": ALL_SKELETONS["CONSTRUCT"]})
    space = asm.config_space()
    by_name = {n.name: n for n in space.nodes}
    assert by_name["greedy_phased.n_phases"].range == (1, 2)
    assert any(c.parent == "greedy_phased.n_phases" for c in by_name["greedy_phased.phase_2"].conditions)
    seen = set()
    for seed in range(60):
        config = space.fold(suggest_from_space(space, RandomTrial(Random(seed))))
        if config.get("constructor") != "greedy_phased":
            continue
        n = config["greedy_phased.n_phases"]
        seen.add(n)
        assert ("greedy_phased.phase_2" in config) == (n >= 2)
        for key in config:  # los parámetros de una fase solo si esa fase está en esa posición
            if key.startswith("greedy_phased.p") and key.count(".") == 3:
                _, pos, phase, _ = key.split(".")
                assert config[f"greedy_phased.phase_{pos[1:]}"] == phase
    assert seen == {1, 2}
    # por defecto, las dos fases en el orden del registro: FRG
    inst = CPMPInstance.cvs_like(5, 5, Random(0))
    config = asm.default_config("CONSTRUCT", {"constructor": "greedy_phased"})
    res = asm.assemble(config)(inst, Random(0), 5.0)
    P = CPMPModel(inst)
    assert res.best_objective == P.objective(FRGConstructor(P, assignment="never").build(inst, Random(0)))


def test_beam_search_over_phases_is_bs_frg_like():
    total_beam = total_greedy = 0
    for k in range(4):
        inst = CPMPInstance.cvs_like(5, 5, Random(k))
        P = CPMPModel(inst)
        total_greedy += P.objective(GreedyConstructor(P, _frg_phases(P)).build(inst, Random(0)))
        total_beam += P.objective(BeamSearchConstructor(P, _frg_phases(P), beam_width=3, branching=10).build(inst, Random(0)))
    assert total_beam <= total_greedy


def test_alone_uses_the_null_phase_when_the_phase_does_not_apply():
    inst = CPMPInstance.cvs_like(4, 4, Random(2))
    P = CPMPModel(inst)
    names = {n for n, _ in phase_trace(alone(BGFill(P)), P.construction_view(inst))}
    assert names == {"fase", "null_phase"}
