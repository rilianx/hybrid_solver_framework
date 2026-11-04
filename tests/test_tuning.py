"""Tuner (§8): evaluación en test, escenario y target-runner de irace."""

from __future__ import annotations

from random import Random

import pytest

from core.assembler import Assembler
from examples.lotsizing.instance import CLSPInstance
from tests.clsp_fixtures import LotSizingModel, clsp_registry
from tuning import evaluate_on_test
from tuning.irace_scenario import parse_irace_params, write_irace_scenario

pytest.importorskip("pulp")


@pytest.fixture(scope="module")
def assembler():
    return Assembler(problem_factory=LotSizingModel, registry=clsp_registry())


@pytest.fixture(scope="module")
def tiny():
    return [CLSPInstance.trigeiro(3, 5, Random(s), utilization=0.9, tbo=2.0) for s in (1, 2)]


def test_evaluate_on_test_compares_against_defaults(assembler, tiny):
    tuned = assembler.default_config("SA")
    report = evaluate_on_test(assembler, tuned, tiny, budget=0.2, seeds=(0, 1),
                              baselines={"default:SA": assembler.default_config("SA"), "default:HYB": assembler.default_config("HYB")},
                              reference=1e6)
    assert len(report.tuned.per_run) == 4 and len(report.tuned.per_instance) == 2
    assert {b.label for b in report.baselines} == {"default:SA", "default:HYB"}
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
    # y la config parseada es ejecutable por el ensamblador
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
    """Con el catálogo generado del flow shop que está en el repo (necesita g++ y pybind11)."""
    import shutil

    pytest.importorskip("pybind11")
    if shutil.which("g++") is None:
        pytest.skip("sin g++")
    from examples.flowshop.pack import PACK
    from scripts.irace_target_runner import main
    from tuning.cli import make_assembler
    from tuning.staged import irace_args

    A, _ = make_assembler(PACK)
    inst = PACK.make_instances(1, 3, PACK.parse_size("10x5"))[0]
    p = tmp_path / "i.txt"
    inst.save(str(p))
    monkeypatch.setenv("HSF_BUDGET", "0.2")
    monkeypatch.setenv("HSF_PROBLEM", "examples.flowshop")
    monkeypatch.delenv("HSF_GENERATED", raising=False)
    rc = main(["7", "1", "123", str(p), *irace_args(A.config_space(), A.default_config("SA"))])
    out = capsys.readouterr().out.strip().splitlines()
    assert rc == 0 and len(out) == 1
    assert float(out[0]) < 1e12


def test_evaluate_with_normalizers_averages_cost_ratios(assembler, tiny):
    cfg = assembler.default_config("ILS")
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

    a = Assembler(problem_factory=LotSizingModel, registry=clsp_registry(), skeletons={"ILS": SKELETONS["ILS"]})
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


def test_paired_comparison_separates_real_differences_from_noise():
    from tuning import paired_comparison
    from tuning.evaluation import ConfigScore

    bk = [100.0] * 6
    mk = lambda label, costs: ConfigScore(label, {}, costs, costs, [[c] for c in costs])  # noqa: E731
    better = mk("a", [101, 102, 101, 103, 102, 101])
    worse = mk("b", [110, 111, 109, 112, 110, 111])
    mixed = mk("c", [95, 110, 99, 107, 96, 108])
    clear = paired_comparison(better, worse, bk)
    assert clear["significant"] and clear["ci95"][0] > 0 and clear["wins_a"] == 6
    noisy = paired_comparison(better, mixed, bk)
    assert not noisy["significant"] and noisy["ci95"][0] < 0 < noisy["ci95"][1]


def test_replica_summary_uses_a_common_best_known_and_averages_the_untuned_baselines(tmp_path):
    """Runs 15-22: dos semillas del tuner difieren en 3-4.5 puntos; el resumen agrega réplicas."""
    import json

    from scripts.tuning_replicas import render

    def score(label, per_instance):
        return {"label": label, "summary": f"SA[{label}]", "per_instance": per_instance}

    def payload(seed, tuned, default, best_known):
        return {"settings": {"trials": 40, "budget": 5, "train": 5, "test": 3, "tuner_seed": seed},
                "test": {"tuned": score("tuned", tuned), "baselines": [score("default:SA", default)],
                         "best_known": best_known}}

    for k, (tuned, default, bk) in enumerate([([110, 120, 100], [115, 125, 110], [100, 100, 100]),
                                               ([130, 100, 95], [116, 124, 108], [100, 98, 100])]):
        (tmp_path / f"r{k}").mkdir()
        (tmp_path / f"r{k}" / "generated.json").write_text(json.dumps(payload(k, tuned, default, bk)))
    md, data = render(tmp_path)
    a = data["generated"]
    assert a["best_known"] == [100, 98, 95]  # mínimo entre réplicas y entre las corridas mismas
    assert [round(r["mean_gap"], 4) for r in a["replicas"]] == [round((10 / 100 + 22 / 98 + 5 / 95) / 3, 4),
                                                                round((30 / 100 + 2 / 98 + 0) / 3, 4)]
    assert a["best_untuned"] == "default:SA" and "Réplicas del tuning (2)" in md
    assert a["tuned_vs_best_untuned"]["replicas_ahead"] == 2  # 12,6 y 10,7 % contra 19,1 %


def test_sa_time_cooling_follows_the_budget_and_old_configs_keep_iteration_cooling():
    """Run 35: el SA enfriaba por iteraciones y con los defaults quedaba frío antes de 1 s."""
    from core.skeleton import SearchState
    from skeletons.sa import _time_cooling_updater

    upd, st = _time_cooling_updater(T0=100.0, T_end=1e-3, budget=10.0), SearchState()
    for t, expected in ((0.0, 100.0), (5.0, 100.0 * 1e-3 ** 0.5), (10.0, 0.1), (30.0, 0.1)):
        st.elapsed_time = t
        upd(st)
        assert abs(st.extra["temperature"] - expected) < 1e-9 * max(1.0, expected)
    from core.assembler import SKELETONS

    assert SKELETONS["SA"].params["cooling"]["values"][0] == "time"  # default
