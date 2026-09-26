"""Etapa de optimización (`llm.optimizer`): una versión más rápida se acepta solo si da las mismas
salidas que la aceptada (el oráculo) y es de verdad más rápida."""

from __future__ import annotations

import types

from core.validation.equivalence import check_component_equivalent, check_parts_equivalent
from examples.cvrp import tour_parts
from examples.cvrp.cases import load_cases
from examples.cvrp.pack import PACK

SLOW_MODEL = '''
import time
from examples.cvrp.tour_parts import *
from examples.cvrp import tour_parts as _t


def cost_terms(inst, sol):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 0.0005:
        pass
    return _t.cost_terms(inst, sol)
'''

FAST_MODEL = "from examples.cvrp.tour_parts import *\n"

SLOW_SWAP = '''
import time
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
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < 0.0005:
            pass
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem):
    return TourSwap(problem)
'''


def test_the_reference_is_equivalent_to_itself_and_a_changed_cost_is_not():
    cases = load_cases()
    instances = [(c.instance, [s["answer"] for s in c.solutions]) for c in cases[:2]]
    assert check_parts_equivalent(tour_parts, tour_parts, instances, n_random=5).passed
    changed = types.SimpleNamespace(**{k: getattr(tour_parts, k) for k in dir(tour_parts) if not k.startswith("_")})
    changed.cost_terms = lambda inst, sol: {"distancia": tour_parts.cost_terms(inst, sol)["distancia"] + 1e-3}
    report = check_parts_equivalent(tour_parts, changed, instances, n_random=5)
    assert not report.passed and "cost_terms_equal" in report.feedback()


def test_a_faster_equivalent_model_replaces_the_accepted_one(tmp_path):
    from examples.cvrp.llm_spec import make_tour_model_spec
    from llm import ScriptedClient
    from llm.optimizer import optimize_model

    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "parts.py").write_text(SLOW_MODEL)
    scale = PACK.make_instances(1, 777, PACK.parse_size("12"))
    client = ScriptedClient(responses=[f"```python\n{FAST_MODEL}\n```"])
    res = optimize_model(client, tmp_path, make_tour_model_spec(), load_cases(), scale, rounds=1, verbose=False)
    assert res.accepted and res.speed_after > 1.5 * res.speed_before, res.reports
    assert (tmp_path / "model" / "parts.py").read_text() == FAST_MODEL
    assert (tmp_path / "model" / "parts_slow.py").read_text() == SLOW_MODEL


def test_a_faster_model_that_changes_outputs_is_rejected(tmp_path):
    from examples.cvrp.llm_spec import make_tour_model_spec
    from llm import ScriptedClient
    from llm.optimizer import optimize_model

    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "parts.py").write_text(SLOW_MODEL)
    wrong = FAST_MODEL + ("from examples.cvrp import tour_parts as _t\n\n\ndef cost_terms(inst, sol):\n"
                          "    return {'distancia': round(_t.cost_terms(inst, sol)['distancia'], 1)}\n")
    client = ScriptedClient(responses=[f"```python\n{wrong}\n```"])
    res = optimize_model(client, tmp_path, make_tour_model_spec(), load_cases(), PACK.make_instances(1, 777, PACK.parse_size("12")),
                         rounds=1, verbose=False)
    assert not res.accepted and (tmp_path / "model" / "parts.py").read_text() == SLOW_MODEL


def test_a_faster_equivalent_neighborhood_becomes_the_next_round(tmp_path):
    from llm import ScriptedClient
    from llm.cycle import load_variant
    from llm.optimizer import optimize_components
    from tests.test_cycle import TOUR_SWAP

    pack = load_variant("cvrp", "tour", None, reference=True)
    (tmp_path / "neighborhood").mkdir()
    (tmp_path / "neighborhood" / "tour_swap_r1.py").write_text(SLOW_SWAP)
    client = ScriptedClient(responses=[f"```python\n{TOUR_SWAP}\n```"])
    out = optimize_components(client, pack, tmp_path, rounds=1, verbose=False)
    row = out["neighborhood/tour_swap"]
    assert row["accepted"] and row["after"] > 1.5 * row["before"], row["rejections"]
    assert (tmp_path / "neighborhood" / "tour_swap_r2.py").read_text().strip() == TOUR_SWAP.strip()


def test_a_neighborhood_with_other_moves_is_not_equivalent():
    from llm.cycle import load_variant

    pack = load_variant("cvrp", "tour", None, reference=True)
    inst = pack.make_instances(1, 5, pack.parse_size("10"))[0]
    P = pack.problem_factory(inst)
    ns: dict = {}
    exec(SLOW_SWAP.replace("t0 < 0.0005", "t0 < 0"), ns)  # noqa: S102
    old = ns["build_component"](P)

    class Reversed(ns["TourSwap"]):
        def moves(self, sol):
            return reversed(list(super().moves(sol)))

    report = check_component_equivalent("neighborhood", old, Reversed(P), P, [tour_parts.trivial_solution(inst)])
    assert not report.passed and "moves_equal" in report.feedback()
