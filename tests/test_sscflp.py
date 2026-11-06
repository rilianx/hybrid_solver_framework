"""SSCFLP: la instancia y sus formatos, el oráculo contra los casos y el benchmark de la literatura con sus referencias."""

from __future__ import annotations

import re
from pathlib import Path
from random import Random

import pytest

from examples.sscflp import model_parts as ref
from examples.sscflp.best_known import load, solve_cbc
from examples.sscflp.cases import brute_force_optimum, load_cases
from examples.sscflp.instance import SSCFLPInstance
from examples.sscflp.pack import PACK

BENCH = Path("examples/sscflp/bench")


def _tiny():
    # 2 centros, 3 clientes: el 0 es barato pero no alcanza para todos
    return SSCFLPInstance(capacity=(5.0, 10.0), fixed=(10.0, 30.0), demand=(3.0, 2.0, 4.0),
                          cost=((1.0, 1.0, 1.0), (5.0, 5.0, 5.0)))


def test_text_roundtrip_is_lossless():
    inst = SSCFLPInstance(capacity=(5.0, 10.0), fixed=(10.5, 30.0), demand=(3.0, 2.0, 4.0),
                          cost=((6739.725, 1.0, 1.0), (5.0, 0.1, 5.0)))
    assert SSCFLPInstance.parse(inst.to_text()) == inst


def test_the_orlib_format_is_by_customer():
    text = "2 3\n5 10\n10 30\n3\n1 5\n2\n1 5\n4\n1 5\n"
    assert SSCFLPInstance.parse_orlib(text) == _tiny()


def test_trailing_data_after_the_cost_matrix_is_ignored():
    # los archivos biobjetivo de MOrepo traen una segunda matriz
    assert SSCFLPInstance.parse(_tiny().to_text() + "9 9 9\n9 9 9\n") == _tiny()


def test_oracle_costs_and_violations():
    inst = _tiny()
    assert ref.cost_terms(inst, ((0, 0, 1),)) == {"apertura": 40.0, "transporte": 7.0}
    assert ref.violations(inst, ((0, 0, 1),)) == {"asignacion": 0.0, "capacidad": 0.0}
    assert ref.violations(inst, ((0, 0, 0),)) == {"asignacion": 0.0, "capacidad": 4.0}
    assert ref.violations(inst, ((0, 0, -1),)) == {"asignacion": 1.0, "capacidad": 0.0}
    assert ref.cost_terms(inst, ((0, 0, -1),)) == {"apertura": 10.0, "transporte": 2.0}
    # abrir solo el 1 cuesta 30 + 15 = 45: más barato que repartir entre los dos (47)
    assert brute_force_optimum(inst) == (45.0, [1, 1, 1])


def test_trivial_falls_back_to_first_fit_decreasing():
    # por costo, el 2 (demanda 4) va al centro 0 y después los de demanda 3 no caben; FFD sí encuentra una
    inst = SSCFLPInstance(capacity=(7.0, 6.0), fixed=(0.0, 0.0), demand=(3.0, 3.0, 4.0, 3.0),
                          cost=((0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0)))
    sol = ref.trivial_solution(inst)
    assert not any(ref.violations(inst, sol).values())


def test_cases_match_brute_force():
    for case in load_cases():
        assert brute_force_optimum(case.instance)[0] == pytest.approx(case.optimum)
        for sc in case.solutions:
            sol = ref.from_answer(case.instance, sc["answer"])
            v = ref.violations(case.instance, sol)
            assert (not any(v.values())) == sc["feasible"]
            if sc["feasible"]:
                assert sum(ref.cost_terms(case.instance, sol).values()) == pytest.approx(sc["cost"])
            else:
                assert all(v[f] > 0 for f in sc["violates"])


def test_generated_instances_have_a_feasible_trivial():
    for inst in PACK.make_instances(4, 0, PACK.parse_size("10x40")) + PACK.make_instances(3, 7, PACK.parse_size(PACK.micro_size)):
        assert not any(ref.violations(inst, ref.trivial_solution(inst)).values())
        sol = ref.random_solution(inst, Random(1))
        assert len(sol) == 1 and len(sol[0]) == inst.n_customers and all(i in inst.facilities for i in sol[0])


def _in_git():
    """Los conjuntos que están en el repositorio (los grandes se bajan con `fetch --large` y git los ignora)."""
    return sorted(p.stem for p in BENCH.glob("*.txt") if not re.fullmatch(r"cap[abc]\d|i\d+_\d+", p.stem))


def test_the_benchmark_is_complete_and_feasible():
    names = _in_git()
    groups = {}
    for n in names:
        g = n.split("-")[0] if "-" in n else "cap"
        groups[g] = groups.get(g, 0) + 1
    assert groups == {"H": 71, "D": 57, "Y": 20, "TB4": 45, "cap": 24}
    bk = load()
    # todas tienen referencia salvo las Díaz-Fernández que CBC no resolvió (no hay tabla publicada)
    assert {n for n in names if not n.startswith("D-")} <= set(bk)
    for n in names:
        inst = SSCFLPInstance.load(str(BENCH / f"{n}.txt"))
        triv = ref.trivial_solution(inst)
        assert not any(ref.violations(inst, triv).values()), n
        if n in bk:
            e = bk[n]
            assert e["lb"] is None or e["lb"] <= e["ub"] + 1e-6
            assert sum(ref.cost_terms(inst, triv).values()) >= e["ub"] - 1e-6, n


def test_references_cover_every_published_instance():
    bk = load()
    assert sum(1 for k in bk if re.fullmatch(r"i\d+_\d+", k)) == 100  # TBED1
    assert sum(1 for k in bk if re.fullmatch(r"cap[abc]\d", k)) == 12
    assert all(bk[f"H-p{k}"]["opt"] for k in range(1, 72))
    assert bk["H-p1"]["ub"] == 8848 and bk["cap61"]["ub"] == 932615.8


def test_published_optima_match_cbc_on_our_conversion():
    # Holmberg p1 (8848) y cap61 (932615.8, redondeado a un decimal en la tabla): la conversión de los archivos y el
    # oráculo reproducen los óptimos publicados
    assert solve_cbc(str(BENCH / "H-p1.txt"), 60)["ub"] == 8848
    assert solve_cbc(str(BENCH / "cap61.txt"), 60)["ub"] == pytest.approx(932615.8, abs=0.06)
