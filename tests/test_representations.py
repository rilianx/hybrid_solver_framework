"""Representaciones alternativas: cada una es un problema distinto para el framework (su pack,
sus componentes, su tuning), con la misma instancia y los mismos casos de prueba que el original.
Aquí: el CVRP como gran tour + Split (`examples/cvrp/tour_parts.py`) contra rutas."""

from __future__ import annotations

import json
import types

import pytest

from core.validation.model_parts import check_heuristic_view, validate_parts
from examples.cvrp import model_parts as routes
from examples.cvrp import tour_parts as tour
from examples.cvrp.cases import load_cases
from examples.cvrp.pack import PACK


@pytest.fixture(scope="module")
def cases():
    return load_cases()


@pytest.fixture(scope="module")
def scale():
    return PACK.make_instances(1, 777, PACK.parse_size(PACK.default_size))


def test_split_cuts_the_tour_optimally_within_capacity(cases):
    for case in cases:
        inst = case.instance
        opt = next(s for s in case.solutions if s["feasible"] and abs(s["cost"] - case.optimum) < 1e-6)
        sol = tour.from_answer(inst, opt["answer"])
        assert not routes.violations(inst, tour.decode(inst, sol))["capacidad"]
        assert sum(tour.cost_terms(inst, sol).values()) <= case.optimum + 1e-6  # el corte óptimo no empeora las rutas


def test_the_tour_representation_passes_the_same_cases_as_a_decoder(cases, scale):
    report = validate_parts(tour, cases, scale_instances=scale, decoder=True)
    assert report.passed, report.feedback()
    # como representación directa no pasa: Split corta mejor que las respuestas de los casos
    assert "cost_matches_cases" in check_heuristic_view(tour, cases).feedback()


def test_a_decoder_cannot_be_worse_than_the_expected_cost(cases):
    m = types.SimpleNamespace(**{k: getattr(tour, k) for k in dir(tour) if not k.startswith("_")})
    m.cost_terms = lambda inst, sol: {"distancia": tour.cost_terms(inst, sol)["distancia"] * 1.01}
    report = check_heuristic_view(m, cases, decoder=True)
    assert not report.passed and "a lo sumo" in report.feedback()


def test_model_specs_carry_the_representation_and_the_prompt_shows_it(cases):
    from examples.cvrp.llm_spec import make_model_spec, make_tour_model_spec
    from llm.parts_generator import heuristic_prompt

    base, alt = make_model_spec(), make_tour_model_spec()
    assert base.representation and not base.decoder and alt.decoder and "GRAN TOUR" in alt.representation
    assert base.answer_format == alt.answer_format and "examples.cvrp.tour_parts" in alt.forbidden_modules
    prompt = heuristic_prompt(alt, cases)
    assert "GRAN TOUR" in prompt and "no sea peor que el esperado" in prompt


def test_compare_packs_uses_a_common_best_known_and_pairs_instances(tmp_path):
    from scripts.compare_packs import compare

    def run(name, rows, bk):
        for k, per in enumerate(rows):
            d = tmp_path / name / f"r{k}"
            d.mkdir(parents=True)
            payload = {"settings": {"size": "30", "seed": 0, "test": 3, "budget": 5},
                       "tuning": {"best_summary": f"SA[{name}]"},
                       "test": {"tuned": {"per_instance": per}, "best_known": bk}}
            (d / "generated.json").write_text(json.dumps(payload))
        return tmp_path / name

    a = run("routes", [[100, 200, 300], [102, 198, 303]], [100, 200, 300])
    b = run("tour", [[99, 210, 320], [101, 205, 310]], [99, 200, 300])
    md, data = compare(a, b)
    assert data["best_known"] == [99, 198, 300]
    assert data["mean_diff"] > 0 and "A `routes`" in md  # rutas mejor en promedio
