"""El ciclo completo (`llm.cycle`): cada representación es un problema con su pack armado sobre las
piezas del modelo (generadas o de referencia), las mismas instancias y los mismos casos."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from random import Random

import pytest

from llm.cycle import load_variant, model_path, run_model_stage

TOUR_SWAP = '''
from examples.cvrp.tour_parts import canonical

COMPONENT = {"name": "tour_swap", "slot": "neighborhood",
             "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"], "requires": [], "params": {}}


class TourSwap:
    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        for i in range(len(sol)):
            for j in range(i + 1, len(sol)):
                yield (i, j)

    def apply(self, sol, m):
        t = list(sol)
        t[m[0]], t[m[1]] = t[m[1]], t[m[0]]
        return canonical(t)

    def undo(self, sol, m):
        return self.apply(sol, m)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem):
    return TourSwap(problem)
'''


ROUTES_CONSTRUCTION = '''
def empty_partial(inst):
    return ((), frozenset(inst.customers))


def candidates(inst, partial):
    routes, pending = partial
    out = []
    for c in sorted(pending):
        for k, r in enumerate(routes):
            if sum(inst.demand[x] for x in r) + inst.demand[c] <= inst.capacity:
                out.append((c, k))
        out.append((c, len(routes)))
    return out


def apply_action(inst, partial, action):
    routes, pending = partial
    c, k = action
    routes = tuple(r + (c,) if i == k else r for i, r in enumerate(routes)) + (((c,),) if k == len(routes) else ())
    return routes, pending - {c}


def is_complete(inst, partial):
    return not partial[1]


def to_solution(inst, partial):
    return canonical(partial[0])


def complete_partial(inst, partial, rng):
    return canonical(partial[0] + tuple((c,) for c in sorted(partial[1])))
'''

NEAREST_NEXT = '''
COMPONENT = {"name": "nearest_next", "slot": "greedy_score", "compatible_skeletons": [], "requires": [], "params": {}}


class NearestNext:
    def __init__(self, problem):
        self.inst = problem.inst

    def score(self, partial, action):
        last = partial[-1] if partial else 0
        return self.inst.dist(last, action)


def build_component(problem):
    return NearestNext(problem)
'''


@pytest.mark.parametrize("variant", ["routes", "tour"])
def test_a_reference_variant_builds_a_pack_that_the_skeletons_can_use(variant):
    from core.assembler import Assembler
    from llm.catalog import build_registry

    pack = load_variant("cvrp", variant, None, reference=True)
    assert pack.name == f"cvrp_{variant}" and len(pack.load_cases()) == 6
    ctx = pack.make_contexts(strict=False)
    assert ctx[0].diversity_probe is not None and ctx[0].trivial_solutions
    A = Assembler(problem_factory=pack.problem_factory, registry=build_registry(pack))
    inst = pack.make_instances(1, 5, pack.parse_size("8"))[0]
    r = A.assemble(A.default_config("FIX_OPT"))(inst, Random(0), 0.5)
    assert pack.problem_factory(inst).is_feasible(r.best_solution)


def test_a_tour_component_is_validated_on_the_tour_model(tmp_path):
    from llm.generator import validate_generated_module

    pack = load_variant("cvrp", "tour", None, reference=True)
    path = tmp_path / "neighborhood" / "tour_swap_r1.py"
    path.parent.mkdir()
    path.write_text(TOUR_SWAP)
    report, _, _ = validate_generated_module(path, pack.make_contexts(strict=False))
    assert report.passed, report.feedback()
    # sobre el modelo de rutas, el mismo componente no sirve: cada representación es otro problema
    routes = load_variant("cvrp", "routes", None, reference=True)
    report, _, _ = validate_generated_module(path, routes.make_contexts(strict=False))
    assert not report.passed


def test_the_model_stage_leaves_an_importable_model_that_the_next_stages_load():
    from llm import ScriptedClient

    from tests.test_model_parts import _ref_sources

    heur, mip = _ref_sources()
    ws = Path("generated") / f"test_cycle_{uuid.uuid4().hex[:8]}"
    try:
        client = ScriptedClient(responses=[f"```python\n{heur}\n```", f"```python\n{mip}\n```",
                                           f"```python\n{ROUTES_CONSTRUCTION}\n```"])
        stats = run_model_stage("cvrp", "routes", ws, client, rounds=1)
        assert stats["accepted"] and stats["construction_accepted"] and model_path(ws).exists()
        pack = load_variant("cvrp", "routes", ws, reference=False)
        assert pack.make_spec().problem_model_import == ".".join(model_path(ws).with_suffix("").parts)
        inst = pack.make_instances(1, 3, pack.parse_size("6"))[0]
        P = pack.problem_factory(inst)
        assert P.is_feasible(P.parts.trivial_solution(inst))
        # con vista constructiva, el ciclo genera puntajes y el prompt de greedy_score trae su código
        assert "def candidates" in pack.make_spec().construction_source
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_a_greedy_score_is_validated_on_the_generated_construction_view(tmp_path):
    from core.construction import GreedyConstructor
    from llm.generator import validate_generated_module

    pack = load_variant("cvrp", "tour", None, reference=True)
    path = tmp_path / "greedy_score" / "nearest_next_r1.py"
    path.parent.mkdir()
    path.write_text(NEAREST_NEXT)
    report, module, _ = validate_generated_module(path, pack.make_contexts(strict=False))
    assert report.passed, report.feedback()
    inst = pack.make_instances(1, 5, pack.parse_size("20"))[0]
    P = pack.problem_factory(inst)
    greedy = GreedyConstructor(P, module.build_component(P)).build(inst, Random(0))
    assert P.is_feasible(greedy) and P.objective(greedy) < P.objective(P.parts.trivial_solution(inst))
