"""Los benchmarks del CVRP (`examples/cvrp/fetch.py`): el X completo, el de FrontierCO y los test de ReEvo."""

from __future__ import annotations

import json
from pathlib import Path

from examples.cvrp import model_parts as ref
from examples.cvrp.fetch import reevo_instances
from examples.cvrp.instance import CVRPInstance

D = Path("examples/cvrp")


def _refs(d: str) -> dict:
    return {k: v for k, v in json.loads((D / d / "best_known.json").read_text()).items() if not k.startswith("_")}


def test_x_is_complete_with_references():
    names = sorted(p.stem for p in (D / "uchoa").glob("X-*.vrp"))
    assert len(names) == 100 and set(names) == set(_refs("uchoa"))
    inst = CVRPInstance.load(str(D / "uchoa" / "X-n1001-k43.vrp"))
    assert inst.n_customers == 1000 and inst.rounded


def test_frontierco_conventions_and_references():
    refs = _refs("frontierco")
    assert len(refs) == 45 and {p.stem for p in (D / "frontierco").glob("*.txt")} == set(refs)
    golden = CVRPInstance.load(str(D / "frontierco" / "Golden_9.txt"))
    arnold = CVRPInstance.load(str(D / "frontierco" / "Leuven1.txt"))
    assert not golden.rounded and arnold.rounded and arnold.n_customers == 3000
    for name in ("Golden_9", "instance_20_1"):
        inst = CVRPInstance.load(str(D / "frontierco" / f"{name}.txt"))
        triv = ref.trivial_solution(inst)
        assert sum(ref.cost_terms(inst, triv).values()) >= refs[name]


def test_reevo_sets_are_the_generator_output():
    gen = reevo_instances()
    assert sorted(gen) == ["test100", "test20", "test50"] and all(len(v) == 64 for v in gen.values())
    for group, insts in gen.items():
        for k in (0, 63):
            assert CVRPInstance.load(str(D / "reevo" / f"{group}_{k:02d}.txt")) == insts[k]
    inst = gen["test50"][0]
    assert inst.capacity == 50 and inst.coords[0] == (0.5, 0.5) and all(1 <= q <= 9 for q in inst.demand[1:])
