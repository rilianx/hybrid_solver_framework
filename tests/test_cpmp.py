"""CPMP: vista constructiva neutral, FRG (Araya y Toledo 2023) como componente de referencia,
BS-FRG como beam search genérica con FRG de rollout, y el `ProblemPack` (generación con un
LLM guionado, validación y esqueleto CONSTRUCT)."""

from __future__ import annotations

import textwrap
from dataclasses import replace
from random import Random

import pytest

from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor
from examples.cpmp.construction import DestinationRank, FRGConstructor, FRGPolicy, Move, best_first
from examples.cpmp.frg import FRG_MINUS, FRGConfig, gen_seq, select_bg_move, stop_reduction, frg
from examples.cpmp.instance import CPMPInstance
from examples.cpmp.layout import Layout
from examples.cpmp.problem_model import CPMPModel, CPMPSolution


# --- problema -------------------------------------------------------------------------
def test_layout_bookkeeping():
    L = Layout([[5, 3, 4], [], [2]], H=4, G=5, track=True)
    assert L.sorted_n == [2, 0, 1] and L.bad() == 1 and not L.is_sorted()
    assert L.g(1) == 5  # una pila vacía vale G
    assert L.ub(0) == 1
    h = L.after(0, 1)
    L.move(0, 1)  # el 4 queda bien puesto sobre el suelo
    assert L.sorted_n == [2, 1, 1] and L.is_sorted() and L.moves == [(0, 1)]
    assert L.state_hash() == h and h in L.visited
    with pytest.raises(ValueError):
        L.move(0, 0)


def test_unblocked_containers():
    # de abajo hacia arriba 8, 5, 6, 1: el 6 y el 1 están desbloqueados (6 ≥ 1), el 5 no
    assert Layout([[8, 5, 6, 1], [], []], H=5, G=8).ub(0) == 2


def test_problem_model_feasibility_and_objective():
    inst = CPMPInstance(((1, 2), (), ()), H=3)
    P = CPMPModel(inst)
    assert not P.is_feasible(CPMPSolution(()))
    assert P.is_feasible(CPMPSolution(((0, 1),))) and P.objective(CPMPSolution(((0, 1),))) == 1
    assert not P.is_feasible(CPMPSolution(((1, 0),)))  # origen vacío
    assert "no está ordenado" in P.explain_infeasibility(CPMPSolution(()))
    with pytest.raises(NotImplementedError):
        P.build_mip(inst)


def test_parse_benchmark_format():
    inst = CPMPInstance.parse("Tiers: 4\nStacks: 3\nContainers: 4\nStack 1: 3 1\nStack 2: 2\nStack 3: 4\n")
    assert inst.H == 4 and inst.stacks == ((3, 1), (2,), (4,)) and inst.N == 4


# --- vista neutral ----------------------------------------------------------------------
def test_view_offers_only_valid_unvisited_single_moves():
    inst = CPMPInstance.cvs_like(4, 5, Random(3))
    P = CPMPModel(inst)
    view = P.construction_view(inst)
    root = view.empty()
    cands = view.candidates(root)
    assert cands and all(isinstance(a, Move) and root.valid(a.so, a.sd) for a in cands)
    assert len(cands) == sum(1 for so in range(inst.S) for sd in range(inst.S) if root.valid(so, sd))
    q = view.apply(root, cands[0])
    assert root.moves == [] and q.moves == [(cands[0].so, cands[0].sd)]
    assert Move(cands[0].sd, cands[0].so) not in view.candidates(q)  # volvería al layout inicial
    assert view.lower_bound(root) == root.bad() and view.key(q) == q.state()


@pytest.mark.parametrize("S,H", [(3, 5), (4, 4), (5, 4), (5, 5)])
def test_neutral_fallback_sorts_small_instances(S, H):
    for k in range(3):
        inst = CPMPInstance.cvs_like(S, H, Random(k))
        P = CPMPModel(inst)
        view = P.construction_view(inst)
        sol = view.complete(view.empty(), Random(0))
        assert P.is_feasible(sol) and view.failures == 0
        assert best_first(Layout.from_instance(inst), Random(0)) is not None


def test_fallback_without_budget_leaves_the_partial_infeasible():
    """Sin último recurso: si el respaldo no alcanza, la construcción queda infactible."""
    inst = CPMPInstance.cvs_like(5, 7, Random(1000))
    P = CPMPModel(inst, fallback_nodes=50)
    view = P.construction_view(inst)
    sol = view.complete(view.empty(), Random(0))
    assert not P.is_feasible(sol) and view.failures == 1


# --- FRG como componente de referencia -------------------------------------------------
def test_bg_move_minimizes_group_difference():
    # el 3 va sobre el 4 (diferencia 1) antes que al suelo (G = 9, diferencia 6)
    assert select_bg_move(Layout([[9, 1, 3], [4], []], H=4, G=9), prevent=False) == (0, 1)


def test_gen_seq_is_lexicographically_largest():
    vals = [5, 3, 4, 3, 1]
    assert [vals[i] for i in gen_seq(vals, 1)] == [5, 4, 3, 1]
    assert gen_seq([1, 2, 3], 2) == []


def test_stop_reduction_when_sr_can_take_everything():
    assert stop_reduction(Layout([[9], [2, 5], [1, 7]], H=4, G=9), sr=0)


@pytest.mark.parametrize("S,H", [(3, 5), (5, 5), (5, 7), (6, 6)])
def test_frg_solves_cvs_like_instances(S, H):
    for k in range(5):
        inst = CPMPInstance.cvs_like(S, H, Random(k))
        P = CPMPModel(inst)
        sol = FRGConstructor(P).build(inst, Random(0))
        assert P.is_feasible(sol) and len(sol.moves) >= Layout.from_instance(inst).bad()


def test_assignment_fallback_rescues_frg_minus():
    """En 3×5 FRG⁻ no termina en algunas instancias; con la asignación de respaldo sí."""
    failed = 0
    for k in range(20):
        inst = CPMPInstance.cvs_like(3, 5, Random(k))
        if not frg(Layout.from_instance(inst), FRG_MINUS)[1]:
            failed += 1
            assert frg(Layout.from_instance(inst), FRGConfig())[1]
    assert failed > 0


def test_frg_does_not_modify_its_input():
    inst = CPMPInstance.cvs_like(4, 6, Random(1))
    L = Layout.from_instance(inst)
    frg(L)
    assert L.moves == [] and L.stacks == [list(s) for s in inst.stacks]


def test_greedy_with_frg_policy_is_frg_when_frg_does_not_revisit_layouts():
    same = 0
    for k in range(6):
        inst = CPMPInstance.cvs_like(5, 6, Random(k))
        P = CPMPModel(inst)
        a = GreedyConstructor(P, FRGPolicy(P)).build(inst, Random(0))
        b = FRGConstructor(P, assignment="never").build(inst, Random(0))
        assert P.is_feasible(a)
        same += a == b
    assert same >= 4


def test_bs_frg_is_the_generic_beam_with_frg_as_rollout():
    total_frg = total_bs = 0
    for k in range(4):
        inst = CPMPInstance.cvs_like(5, 6, Random(k))
        P = CPMPModel(inst)
        f = P.objective(FRGConstructor(P).build(inst, Random(0)))
        bs = BeamSearchConstructor(P, DestinationRank(P), rollout=FRGPolicy(P), beam_width=3, branching=2 * inst.S)
        sol = bs.build(inst, Random(0))
        assert P.is_feasible(sol) and Layout.from_instance(inst).bad() <= P.objective(sol)
        total_frg, total_bs = total_frg + f, total_bs + P.objective(sol)
    assert total_bs < total_frg


# --- pack: catálogo, esqueleto CONSTRUCT, validación y generación ----------------------
def test_catalog_wraps_scores_as_greedy_and_beam_constructors():
    from examples.cpmp.catalog import build_registry

    names = {s.name for s in build_registry().for_slot("constructor")}
    assert {"best_first", "frg", "greedy_frg_policy", "beam_frg_policy", "greedy_destination_rank"} <= names


def test_construct_skeleton_evaluates_constructors():
    from core.assembler import ALL_SKELETONS, Assembler
    from examples.cpmp.catalog import build_registry
    from examples.cpmp.pack import PACK

    a = Assembler(problem_factory=PACK.problem_factory, registry=build_registry(),
                  skeletons={"CONSTRUCT": ALL_SKELETONS["CONSTRUCT"]})
    assert [n for n in a.config_space().nodes if n.name == "skeleton"][0].values == ("CONSTRUCT",)
    insts = PACK.make_instances(2, 0, PACK.parse_size("5x5"))
    lb = sum(Layout.from_instance(i).bad() for i in insts) / 2
    for name in ("best_first", "frg", "greedy_frg_policy", "beam_frg_policy"):
        cfg = a.default_config("CONSTRUCT", {"constructor": name})
        assert lb <= a.evaluate(cfg, insts, 1.0, on_error="raise") < a.penalty_cost
    run = a.assemble({**a.default_config("CONSTRUCT", {"constructor": "best_first"}), "CONSTRUCT.multistart": True})
    assert run(insts[0], Random(0), 0.2).iterations > 1


def test_validation_accepts_frg_policy_and_rejects_a_myopic_score():
    from core.validation import validate_component
    from examples.cpmp.pack import PACK

    comp = lambda name, slot="greedy_score": {"name": name, "slot": slot, "compatible_skeletons": ["CONSTRUCT"], "params": {}}  # noqa: E731
    ctxs = PACK.make_contexts()
    for c in ctxs:
        r = validate_component(comp("frg_policy", "construction_policy"), FRGPolicy(c.problem), c)
        assert r.passed, r.feedback()
    reports = [validate_component(comp("destination_rank"), DestinationRank(c.problem), c) for c in ctxs]
    assert not all(r.passed for r in reports)
    assert any("not_much_worse_than_trivial" in r.feedback() for r in reports if not r.passed)


def test_prompt_describes_the_neutral_view_without_frg():
    from examples.cpmp.llm_spec import make_spec
    from llm.prompts import generation_prompt

    p = generation_prompt(make_spec(), "greedy_score", 3)
    assert "CPMP" in p and "class Move" in p and "class Layout" in p
    assert "frg" not in p.lower() and "fill-and-reduce" not in p.lower()


IMPURE = textwrap.dedent('''
    COMPONENT = {"name": "unbury_lowest", "slot": "greedy_score", "compatible_skeletons": ["CONSTRUCT"],
                 "requires": [], "params": {}}


    class UnburyLowest:
        def __init__(self, problem):
            self.problem = problem

        def score(self, partial, action):
            partial.moves.append((action.so, action.sd))  # error: modifica el parcial
            return float(partial.h(action.so))


    def build_component(problem, **params):
        return UnburyLowest(problem)
''')

FIXED = "\n".join(line for line in IMPURE.splitlines() if "modifica el parcial" not in line)


def test_generation_cycle_on_cpmp(tmp_path):
    from examples.cpmp.pack import PACK
    from llm import ScriptedClient, generate_slot

    fence = lambda s: f"Variante:\n```python\n{s}\n```"  # noqa: E731
    # umbral de calidad laxo: este test ejercita el ciclo generar → validar → corregir, no la calidad
    ctxs = [replace(c, constructor_max_relative_gap=50.0, diversity_probe=None) for c in PACK.make_contexts(n_contexts=1)]
    client = ScriptedClient(responses=[fence(IMPURE), fence(FIXED)])
    accepted, stats = generate_slot(client, PACK.make_spec(), "greedy_score", 1, ctxs, tmp_path, max_rounds=2, verbose=False)
    assert [c.name for c in accepted] == ["unbury_lowest"]
    assert stats.rejections_by_layer == {"contractual": 1} and stats.rounds_per_accepted == {"unbury_lowest": 2}
    assert "greedy_score.pure" in client.calls[1][1]
    impl = accepted[0].build_component(ctxs[0].problem)
    inst = ctxs[0].instances[0]
    assert ctxs[0].problem.is_feasible(GreedyConstructor(ctxs[0].problem, impl).build(inst, Random(0)))
