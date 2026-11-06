"""Mochila multidimensional: la instancia, el oráculo contra los casos y los benchmarks (OR-Library y ReEvo)."""

from __future__ import annotations

import json
from pathlib import Path
from random import Random

import pytest

from examples.mkp import model_parts as ref
from examples.mkp.cases import brute_force_optimum, load_cases
from examples.mkp.fetch import parse_orlib, reevo_instances
from examples.mkp.instance import MKPInstance
from examples.mkp.pack import PACK

D = Path("examples/mkp/orlib")


def _tiny():
    # 3 ítems, 2 recursos: 0 y 1 juntos exceden el recurso 0
    return MKPInstance(profit=(10.0, 7.0, 4.0), weight=((5.0, 6.0, 1.0), (1.0, 1.0, 1.0)), capacity=(10.0, 3.0))


def test_text_roundtrip_and_orlib_format():
    inst = MKPInstance(profit=(0.25, 7.0), weight=((0.1, 0.2), (1.0, 3.0)), capacity=(1.0, 3.5))
    assert MKPInstance.parse(inst.to_text()) == inst
    # mknapcb: K casos; cada uno `n m opt`, beneficios, m filas de consumos, capacidades
    assert parse_orlib("1\n3 2 14\n10 7 4\n5 6 1\n1 1 1\n10 3\n") == [_tiny()]


def test_oracle_costs_and_violations():
    inst = _tiny()
    assert ref.cost_terms(inst, ((1, 0, 1),)) == {"beneficio": -14.0}
    assert ref.violations(inst, ((1, 0, 1),)) == {"capacidad": 0.0}
    assert ref.violations(inst, ((1, 1, 0),))["capacidad"] == pytest.approx(1 + 1 / 10)
    assert brute_force_optimum(inst) == (-14.0, [1, 0, 1])
    assert ref.trivial_solution(inst) in {((1, 0, 1),), ((0, 1, 1),)}


def test_cases_match_brute_force():
    for case in load_cases():
        assert brute_force_optimum(case.instance)[0] == pytest.approx(case.optimum)
        for sc in case.solutions:
            sol = ref.from_answer(case.instance, sc["answer"])
            v = ref.violations(case.instance, sol)
            assert (not any(v.values())) == sc["feasible"]
            if sc["feasible"]:
                assert sum(ref.cost_terms(case.instance, sol).values()) == pytest.approx(sc["cost"])


def test_generated_instances():
    for inst in PACK.make_instances(3, 0, PACK.parse_size("50x5")):
        assert not any(ref.violations(inst, ref.trivial_solution(inst)).values())
        assert len(ref.random_solution(inst, Random(1))[0]) == inst.n_items


def test_orlib_is_complete_and_consistent_with_its_references():
    refs = {k: v for k, v in json.loads((D / "best_known.json").read_text()).items() if not k.startswith("_")}
    assert len(refs) == 7 + 48 + 270 and {p.stem for p in D.glob("*.txt")} == set(refs)
    for name, best in refs.items():  # la greedy nunca supera la mejor conocida (mknap2 leída por recurso)
        inst = MKPInstance.load(str(D / f"{name}.txt"))
        assert sum(ref.cost_terms(inst, ref.trivial_solution(inst)).values()) >= best - 1e-6, name
    cb = MKPInstance.load(str(D / "mknapcb9_30.txt"))
    assert (cb.n_items, cb.n_resources) == (500, 30) and refs["mknap2_03"] == -141278


def test_reevo_sets_reproduce_the_generator():
    gen = reevo_instances()
    assert sorted(gen, key=lambda k: int(k[4:])) == ["test100", "test200", "test300", "test500", "test1000"]
    inst = gen["test100"][0]
    assert inst.capacity == (1.0,) * 5 and inst.n_items == 100
    assert all(max(row) <= 1.0 for row in inst.weight)  # cada consumo cabe solo
    reevo = Path("examples/mkp/reevo/test100_00.txt")
    if reevo.exists():
        assert MKPInstance.load(str(reevo)) == inst


def test_reevo_references_are_proven_optima():
    refs = json.loads(Path("examples/mkp/reevo_best_known.json").read_text())
    assert len(refs) == 5 * 64 and all(v["opt"] for v in refs.values())
    mean100 = -sum(v["ub"] for k, v in refs.items() if k.startswith("test100_")) / 64
    assert mean100 == pytest.approx(23.346, abs=1e-3)  # MCTS-AHD publica 23.269 en MKP100 (tabla 2)


def test_the_normalized_generator_matches_the_reevo_distribution():
    inst = PACK.make_instances(1, 0, PACK.parse_size("n100x5"))[0]
    assert inst.capacity == (1.0,) * 5 and inst.n_items == 100
    assert all(0 < w <= 1 for row in inst.weight for w in row)
    assert PACK.parse_size("100x5") == {"items": 100, "resources": 5}
