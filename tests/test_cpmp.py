"""CPMP: FRG (Araya y Toledo 2023), su vista constructiva y BS-FRG sobre la beam search genérica."""

from __future__ import annotations

from random import Random

import pytest

from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor
from examples.cpmp.construction import FillFirst, FRGConstructor, FRGPolicy, FRGStep, Move, Reduce
from examples.cpmp.frg import FRG_MINUS, FRGConfig, Layout, frg, gen_seq, select_bg_move, stop_reduction
from examples.cpmp.instance import CPMPInstance
from examples.cpmp.problem_model import CPMPModel, CPMPSolution


def test_layout_bookkeeping():
    L = Layout([[5, 3, 4], [], [2]], H=4, G=5)
    assert L.sorted_n == [2, 0, 1] and L.bad() == 1 and not L.is_sorted()
    assert L.g(1) == 5  # una pila vacía vale G
    assert L.ub(0) == 1
    L.move(0, 1)  # el 4 queda bien puesto sobre el suelo
    assert L.sorted_n == [2, 1, 1] and L.is_sorted() and L.moves == [(0, 1)]
    with pytest.raises(ValueError):
        L.move(0, 0)


def test_unblocked_containers_follow_definition_1():
    # de abajo hacia arriba 8, 5, 6, 1: el 6 y el 1 están desbloqueados (6 ≥ 1), el 5 no
    L = Layout([[8, 5, 6, 1], [], []], H=5, G=8)
    assert L.ub(0) == 2


def test_bg_move_minimizes_group_difference():
    # el 3 va sobre el 4 (diferencia 1) antes que al suelo (G = 9, diferencia 6)
    L = Layout([[9, 1, 3], [4], []], H=4, G=9)
    assert select_bg_move(L, prevent=False) == (0, 1)


def test_gen_seq_is_lexicographically_largest():
    assert [v for v in (lambda vals: [vals[i] for i in gen_seq(vals, 1)])([5, 3, 4, 3, 1])] == [5, 4, 3, 1]
    assert gen_seq([1, 2, 3], 2) == []


def test_stop_reduction_when_sr_can_take_everything():
    L = Layout([[9], [2, 5], [1, 7]], H=4, G=9)
    L.sr = 0
    assert stop_reduction(L)


@pytest.mark.parametrize("S,H", [(3, 5), (5, 5), (5, 7), (6, 6)])
def test_frg_solves_cvs_like_instances(S, H):
    for k in range(5):
        inst = CPMPInstance.cvs_like(S, H, Random(k))
        P = CPMPModel(inst)
        sol = FRGConstructor().build(inst, Random(0))
        assert P.is_feasible(sol)
        assert len(sol.moves) >= Layout.from_instance(inst).bad()


def test_assignment_fallback_rescues_frg_minus():
    """En 3×5 FRG⁻ no termina en algunas instancias; con la asignación de respaldo sí."""
    failed = 0
    for k in range(20):
        inst = CPMPInstance.cvs_like(3, 5, Random(k))
        if frg(Layout.from_instance(inst), FRG_MINUS).dead:
            failed += 1
            assert not frg(Layout.from_instance(inst), FRGConfig()).dead
    assert failed > 0


def test_frg_does_not_modify_its_input():
    inst = CPMPInstance.cvs_like(4, 6, Random(1))
    L = Layout.from_instance(inst)
    frg(L)
    assert L.moves == [] and L.stacks == [list(s) for s in inst.stacks]


def test_problem_model_feasibility_and_objective():
    inst = CPMPInstance(((1, 2), (), ()), H=3)
    P = CPMPModel(inst)
    assert not P.is_feasible(CPMPSolution(()))
    assert P.is_feasible(CPMPSolution(((0, 1),))) and P.objective(CPMPSolution(((0, 1),))) == 1
    assert not P.is_feasible(CPMPSolution(((1, 0),)))  # origen vacío
    assert "no está ordenado" in P.explain_infeasibility(CPMPSolution(()))


def test_parse_benchmark_format():
    inst = CPMPInstance.parse("Tiers: 4\nStacks: 3\nContainers: 4\nStack 1: 3 1\nStack 2: 2\nStack 3: 4\n")
    assert inst.H == 4 and inst.stacks == ((3, 1), (2,), (4,)) and inst.N == 4


def test_view_actions():
    inst = CPMPInstance.cvs_like(4, 5, Random(3))
    P = CPMPModel(inst)
    view = P.construction_view(inst, k=2)
    root = view.empty()
    cands = view.candidates(root)
    assert FRGStep() in cands and any(isinstance(a, Reduce) for a in cands)
    moves = [a for a in cands if isinstance(a, Move)]
    assert max(sum(1 for m in moves if m.so == s) for s in range(inst.S)) <= 2
    q = view.apply(root, moves[0])
    assert root.moves == [] and q.moves == [(moves[0].so, moves[0].sd)]
    assert Move(moves[0].sd, moves[0].so) not in view.candidates(q)  # no se deshace el último
    assert view.lower_bound(root) == root.bad()
    r = view.apply(root, next(a for a in cands if isinstance(a, Reduce)))
    assert len(r.moves) >= 1 and r.sr is None


def test_greedy_with_frg_policy_is_frg_when_it_terminates():
    for k in range(5):
        inst = CPMPInstance.cvs_like(5, 6, Random(k))
        P = CPMPModel(inst)
        a = GreedyConstructor(P, FRGPolicy(P)).build(inst, Random(0))
        b = FRGConstructor(assignment="never").build(inst, Random(0))
        assert P.is_feasible(a) and a == b


def test_bs_frg_improves_frg_and_respects_lower_bound():
    total_frg = total_bs = 0
    for k in range(4):
        inst = CPMPInstance.cvs_like(5, 6, Random(k))
        P = CPMPModel(inst)
        f = P.objective(FRGConstructor().build(inst, Random(0)))
        sol = BeamSearchConstructor(P, rollout="complete", beam_width=3).build(inst, Random(0))
        assert P.is_feasible(sol) and Layout.from_instance(inst).bad() <= P.objective(sol) <= f
        total_frg, total_bs = total_frg + f, total_bs + P.objective(sol)
    assert total_bs < total_frg


def test_single_moves_only_beam_and_fill_first_greedy():
    inst = CPMPInstance.cvs_like(4, 6, Random(7))
    P = CPMPModel(inst)
    bs = BeamSearchConstructor(P, rollout="complete", beam_width=2,
                               view_params={"compound": False, "frg_action": False})
    assert P.is_feasible(bs.build(inst, Random(0)))
    assert P.is_feasible(GreedyConstructor(P, FillFirst(P)).build(inst, Random(0)))
    classic = BeamSearchConstructor(P, FillFirst(P), evaluation="score", beam_width=3)
    assert P.is_feasible(classic.build(inst, Random(0)))
