"""Tuner (§8): Optuna sobre el espacio condicional, evaluación en test e irace."""

from __future__ import annotations

from random import Random

import pytest

from core.assembler import Assembler
from examples.lotsizing.catalog import build_registry
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel
from tuning import evaluate_on_test, tune_with_optuna
from tuning.irace_scenario import parse_irace_params, write_irace_scenario

pytest.importorskip("optuna")


@pytest.fixture(scope="module")
def assembler():
    return Assembler(problem_factory=LotSizingModel, registry=build_registry())


@pytest.fixture(scope="module")
def tiny():
    return [CLSPInstance.trigeiro(3, 5, Random(s), utilization=0.9, tbo=2.0) for s in (1, 2)]


def test_optuna_tunes_conditional_space_and_enqueues_defaults(assembler, tiny):
    n_sk = len(assembler.available_skeletons())
    result = tune_with_optuna(assembler, tiny, budget=0.2, n_trials=n_sk + 3, seed=1)
    assert len(result.trials) == n_sk + 3
    # los primeros trials son los defaults de cada esqueleto, uno por esqueleto
    assert [t.enqueued for t in result.trials[:n_sk]] == [True] * n_sk
    assert {t.config["skeleton"] for t in result.trials[:n_sk]} == set(assembler.available_skeletons())
    # los muestreados respetan la condicionalidad: solo parámetros del esqueleto elegido
    for t in result.trials[n_sk:]:
        sk = t.config["skeleton"]
        assert all(k.split(".")[0] == sk for k in t.config if k.split(".")[0] in assembler.skeletons), t.config
        if sk != "ILS":
            assert "perturbation" not in t.config
    assert result.best_cost == min(t.cost for t in result.trials) < assembler.penalty_cost
    curve = result.incumbent_curve()
    assert curve == sorted(curve, reverse=True) and curve[-1] == result.best_cost
    d = result.to_dict()
    assert d["n_trials"] == n_sk + 3 and d["best_default_cost"] is not None and d["skeleton_usage"]


def test_evaluate_on_test_compares_against_defaults(assembler, tiny):
    tuned = assembler.default_config("SA")
    report = evaluate_on_test(assembler, tuned, tiny, budget=0.2, seeds=(0, 1),
                              baselines={"default:SA": assembler.default_config("SA"), "default:LNS_MIP": assembler.default_config("LNS_MIP")},
                              reference=1e6)
    assert len(report.tuned.per_run) == 4 and len(report.tuned.per_instance) == 2
    assert {b.label for b in report.baselines} == {"default:SA", "default:LNS_MIP"}
    assert report.best_baseline().mean <= max(b.mean for b in report.baselines)
    d = report.to_dict()
    assert d["wins_per_instance"].endswith("/2") and "gain_vs_best_baseline" in d


def test_irace_params_are_typed_from_the_space(assembler):
    space = assembler.config_space()
    cfg = parse_irace_params(space, ["--skeleton=SA", "--constructor=lot_for_lot", "--neighborhood", "setup_flip",
                                     "--SA.T0=12.5", "--SA.alpha=0.95", "--SA.iters_per_T=7"])
    assert cfg["skeleton"] == "SA" and cfg["neighborhood"] == "setup_flip"
    assert isinstance(cfg["SA.iters_per_T"], int) and cfg["SA.iters_per_T"] == 7
    assert isinstance(cfg["SA.T0"], float) and cfg["SA.T0"] == 12.5
    with pytest.raises(ValueError):
        parse_irace_params(space, ["--no_existe=1"])
    # y la config parseada es ejecutable por el mismo target runner que usa Optuna
    inst = CLSPInstance.trigeiro(3, 5, Random(1), utilization=0.9, tbo=2.0)
    assert assembler.evaluate(cfg, [inst], 0.2) < assembler.penalty_cost


def test_irace_scenario_files(assembler, tiny, tmp_path):
    paths = []
    for k, inst in enumerate(tiny):
        p = tmp_path / f"inst_{k}.txt"
        inst.save(str(p))
        paths.append(p)
    scenario = write_irace_scenario(assembler.config_space(), tmp_path / "irace", paths, budget=1.0, max_experiments=50)
    text = scenario.read_text()
    assert "parameterFile" in text and "targetRunner" in text and "maxExperiments = 50" in text
    params = (tmp_path / "irace" / "parameters.txt").read_text()
    assert "skeleton" in params and '%in%' in params
    assert (tmp_path / "irace" / "instances.txt").read_text().count("\n") == 2
    runner = (tmp_path / "irace" / "target-runner").read_text()
    assert "HSF_BUDGET=1.0" in runner and "scripts.irace_target_runner" in runner


def test_target_runner_prints_a_single_cost(tmp_path, monkeypatch, capsys):
    from scripts.irace_target_runner import main

    inst = CLSPInstance.trigeiro(3, 5, Random(1), utilization=0.9, tbo=2.0)
    p = tmp_path / "i.txt"
    inst.save(str(p))
    monkeypatch.setenv("HSF_BUDGET", "0.2")
    monkeypatch.delenv("HSF_GENERATED", raising=False)
    rc = main(["7", "1", "123", str(p), "--skeleton=LNS_MIP", "--constructor=lot_for_lot", "--destruction=random_setups"])
    out = capsys.readouterr().out.strip().splitlines()
    assert rc == 0 and len(out) == 1
    assert float(out[0]) < 1e12


def test_evaluate_with_normalizers_averages_cost_ratios(assembler, tiny):
    cfg = assembler.default_config("LNS_MIP")
    raw = [assembler.evaluate(cfg, [inst], 0.2, seed=k) for k, inst in enumerate(tiny)]
    refs = [2.0 * raw[0], 4.0 * raw[1]]
    ratio = assembler.evaluate(cfg, tiny, 0.2, seed=0, normalizers=refs)
    assert ratio == pytest.approx((0.5 + 0.25) / 2, rel=0.05)
    with pytest.raises(ValueError):
        assembler.evaluate(cfg, tiny, 0.2, normalizers=[1.0])


def test_gap_against_best_known_weighs_instances_equally():
    from tuning.evaluation import ConfigScore, TestReport, best_known_costs

    # instancia 0 de escala 100, instancia 1 de escala 10 000: en bruto domina la 1
    a = ConfigScore("a", {"skeleton": "SA"}, [110.0, 10000.0], [110.0, 10000.0], [[110.0], [10000.0]])
    b = ConfigScore("b", {"skeleton": "ILS"}, [100.0, 10500.0], [100.0, 10500.0], [[100.0], [10500.0]])
    fail = ConfigScore("f", {"skeleton": "TS"}, [1e12, 1e12], [1e12, 1e12], [[1e12], [1e12]])
    bk = best_known_costs([a, b, fail], external=[None, 9000.0], penalty_cost=1e12)
    assert bk == [100.0, 9000.0]  # la fallida no cuenta; el MIP externo gana en la instancia 1
    assert a.gaps(bk) == pytest.approx([0.10, 1000 / 9000])
    assert b.mean_gap(bk) == pytest.approx((0.0 + 1500 / 9000) / 2)
    assert fail.n_failed(1e12) == 2
    d = TestReport(tuned=a, baselines=[b, fail], best_known=bk).to_dict()
    assert d["best_known"] == bk and d["best_baseline_by_gap"] == "b"
    assert d["tuned"]["mean_gap"] == pytest.approx(a.mean_gap(bk))


def test_one_slot_baselines_vary_one_slot_at_a_time():
    from core.assembler import SKELETONS
    from tuning import one_slot_baselines

    a = Assembler(problem_factory=LotSizingModel, registry=build_registry(), skeletons={"ILS": SKELETONS["ILS"]})
    base = one_slot_baselines(a)
    default = a.default_config("ILS")
    assert base["default:ILS"] == default
    for label, cfg in base.items():
        if label == "default:ILS":
            continue
        slot, name = label.split(":", 1)[1].split("=")
        assert cfg[slot] == name != default[slot]
        others = {s for s in ("constructor", "neighborhood", "perturbation") if s != slot}
        assert all(cfg[s] == default[s] for s in others), label


def test_optuna_with_restricted_skeletons_only_samples_those(tiny):
    from core.assembler import SKELETONS

    a = Assembler(problem_factory=LotSizingModel, registry=build_registry(),
                  skeletons={k: SKELETONS[k] for k in ("SA", "VNS")})
    result = tune_with_optuna(a, tiny, budget=0.2, n_trials=5, seed=0, normalizers=[1e5, 1e5])
    assert {t.config["skeleton"] for t in result.trials} <= {"SA", "VNS"}
    assert result.best_cost < 1.0  # costos normalizados, no en bruto


def test_mip_time_share_is_not_floored_to_one_second(assembler, tiny, monkeypatch):
    import core.assembler as asm

    seen = []
    real = asm.build_lns_mip
    monkeypatch.setattr(asm, "build_lns_mip", lambda *a, **kw: seen.append(kw["mip_time_limit"]) or real(*a, **kw))
    for share in (0.1, 0.5):
        cfg = dict(assembler.default_config("LNS_MIP"), **{"LNS_MIP.mip_time_share": share})
        assembler.evaluate(cfg, tiny[:1], budget=4.0)
    assert seen == pytest.approx([0.4, 2.0])  # antes: max(1.0, ·) → 1.0 y 2.0, y CBC redondeaba
    assert asm.MIN_MIP_SECONDS < 1.0
    assert assembler.default_config("LNS_MIP")["LNS_MIP.mip_time_share"] == pytest.approx(0.2)


def test_generated_only_catalog_drops_handwritten_in_generated_slots():
    from examples.lotsizing.catalog import load_generated

    gen = load_generated("generated/clsp", revalidate=False, verbose=False)
    assert gen, "se espera el catálogo de la corrida 8 en generated/clsp"
    only = build_registry(gen, handwritten=False)
    gen_slots = {c.slot for c in gen}
    for slot in gen_slots:
        names = {s.name for s in only.for_slot(slot)}
        assert names and names <= {c.name for c in gen}, slot
    # slots que el LLM no genera conservan el de mano, así FIX_OPT sigue existiendo
    assert {s.name for s in only.for_slot("fixing_policy")} == {"sliding_window"}
    assert {s.name for s in build_registry(gen).for_slot("neighborhood")} >= {"setup_flip"}
