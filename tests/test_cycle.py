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
        client = ScriptedClient(responses=[f"```python\n{heur}\n```", f"```python\n{mip}\n```"])
        stats = run_model_stage("cvrp", "routes", ws, client, rounds=1)
        assert stats["accepted"] and model_path(ws).exists() and (ws / "model_stats.json").exists()
        pack = load_variant("cvrp", "routes", ws, reference=False)
        assert pack.make_spec().problem_model_import == ".".join(model_path(ws).with_suffix("").parts)
        inst = pack.make_instances(1, 3, pack.parse_size("6"))[0]
        P = pack.problem_factory(inst)
        assert P.is_feasible(P.parts.trivial_solution(inst))
    finally:
        shutil.rmtree(ws, ignore_errors=True)
