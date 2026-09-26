"""Generación del ProblemModel completo con LLM (§6.1): validación semántica, corrección y
chequeo cruzado contra el modelo de referencia."""

from __future__ import annotations

import textwrap
from random import Random

from examples.cvrp.problem_model import CVRPModel
from llm import ScriptedClient
from llm.model_generator import ModelSpec, cross_check, generate_problem_model, validate_model_module

HEADER = textwrap.dedent("""
    from random import Random
    from examples.cvrp.problem_model import CVRPModel, route_length
    from examples.cvrp.components import SingletonRoutes
""")
GOOD = HEADER + textwrap.dedent("""
    def build_problem_model(inst):
        return CVRPModel(inst)
    def trivial_solution(inst):
        return SingletonRoutes().build(inst, Random(0))
""")
# olvida el tramo de vuelta al depósito: las dos vistas dejan de coincidir
BAD = HEADER + textwrap.dedent("""
    class M(CVRPModel):
        def distance(self, sol):
            return sum(route_length(self.inst, r) - self.inst.dist(r[-1], 0) for r in sol if r)
    def build_problem_model(inst):
        return M(inst)
    def trivial_solution(inst):
        return SingletonRoutes().build(inst, Random(0))
""")


def _micro():
    from examples.cvrp.pack import PACK

    return PACK.make_instances(2, 900, {"customers": 6})


def _spec(forbidden=()):
    return ModelSpec(name="cvrp", description="...", instance_source="", instance_import="examples.cvrp.instance",
                     forbidden_modules=list(forbidden))


def test_semantic_layer_rejects_views_that_disagree_and_the_llm_gets_the_report(tmp_path):
    client = ScriptedClient(responses=[f"```python\n{BAD}\n```", f"```python\n{GOOD}\n```"])
    res = generate_problem_model(client, _spec(), _micro(), tmp_path, max_rounds=3, verbose=False)
    assert res.path is not None and res.rounds == 2 and res.llm_calls == 2
    assert "objective_agreement" in res.reports[0]
    assert "RECHAZADO" in client.calls[1][1] and "objective_agreement" in client.calls[1][1]


def test_forbidden_imports_block_copying_the_reference_model(tmp_path):
    path = tmp_path / "m.py"
    path.write_text(GOOD)
    report, module = validate_model_module(path, _micro(), forbidden_modules=["examples.cvrp.problem_model"])
    assert not report.passed and module is None and "no_forbidden_imports" in report.feedback()


def test_cross_check_compares_mip_optima_with_the_reference(tmp_path):
    path = tmp_path / "m.py"
    path.write_text(GOOD)
    report, module = validate_model_module(path, _micro())
    assert report.passed
    rows = cross_check(module, CVRPModel, _micro(), time_limit=10)
    assert all(r["match"] for r in rows) and all(r["generated"] > 0 for r in rows)


def test_cvrp_pack_prompt_shows_the_instance_but_not_the_reference_model():
    from examples.cvrp.pack import PACK
    from llm.model_generator import model_prompt

    spec = PACK.make_model_spec()
    prompt = model_prompt(spec)
    assert "class CVRPInstance" in prompt and "class CVRPModel" not in prompt
    assert "examples.cvrp.problem_model" in spec.forbidden_modules
