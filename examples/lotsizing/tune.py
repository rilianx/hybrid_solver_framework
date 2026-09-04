"""Tuning real sobre el CLSP (§8) y la pregunta de §10: ¿el catálogo ampliado con
componentes generados por LLM **ayuda o diluye**?

    python -m examples.lotsizing.tune --trials 30 --budget 5 --train 3 --test 3 --catalog both

Para cada catálogo (`handwritten` = solo componentes a mano, `all` = + generados):
1. Optuna (TPE) sobre el espacio completo, con los defaults de cada esqueleto
   encolados como primeros trials.
2. La mejor configuración se evalúa en instancias de TEST (no vistas), con 3
   semillas, contra el default de cada esqueleto.
3. Se guarda `tuning_out/<catalog>.json` y se imprime la comparación.

Con `--irace DIR` además escribe un escenario irace listo para correr afuera.

Todas las instancias son Trigeiro con la misma utilización/TBO; las de test usan
semillas disjuntas. El presupuesto por corrida es el mismo en tuning y en test.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from random import Random
from statistics import mean

from core.assembler import Assembler, describe
from tuning import evaluate_on_test, tune_with_optuna

from .catalog import build_registry, load_generated
from .components import LotForLotConstructor
from .problem_model import CLSPInstance, LotSizingModel


def make_instances(n: int, items: int, periods: int, seed0: int, utilization: float = 0.95, tbo: float = 3.0):
    return [CLSPInstance.trigeiro(items, periods, Random(seed0 + k), utilization=utilization, tbo=tbo) for k in range(n)]


def make_assembler(catalog: str, generated_dir: str, verbose: bool = False) -> tuple[Assembler, list[str]]:
    generated = load_generated(generated_dir, verbose=verbose) if catalog == "all" else []
    registry = build_registry(generated)
    return Assembler(problem_factory=LotSizingModel, registry=registry), [c.name for c in generated]


def run_experiment(catalog: str, args, train, test, out_dir: Path) -> dict:
    assembler, gen_names = make_assembler(catalog, args.generated, verbose=True)
    space = assembler.config_space()
    n_gen_in_space = sum(1 for n in space.nodes if n.type == "cat" for v in n.values if v in gen_names)
    print(f"\n=== catálogo `{catalog}`: {len(space.nodes)} parámetros, {n_gen_in_space} opciones generadas por LLM ===")

    def on_trial(t):
        mark = "*" if t.enqueued else " "
        print(f"  trial {t.number:>3}{mark} {t.cost:>12.1f}  {t.summary}")

    result = tune_with_optuna(assembler, train, args.budget, args.trials, seed=args.seed, space=space, on_trial=on_trial)
    print(f"  mejor en train: {result.best_cost:.1f}  {describe(result.best_config)}  ({result.seconds:.0f}s, {result.n_failed} fallidas)")

    reference = mean(LotSizingModel(i).objective(LotForLotConstructor().build(i, Random(0))) for i in test)
    report = evaluate_on_test(assembler, result.best_config, test, args.budget, seeds=tuple(range(args.seeds)), reference=reference)
    print(f"  TEST (lot-for-lot sin búsqueda = {reference:.1f}):")
    rows = [("tuned", report.tuned)] + [(b.label, b) for b in sorted(report.baselines, key=lambda s: s.mean)]
    for label, sc in rows:
        print(f"    {label:<22} {sc.mean:>12.1f} ± {sc.std:>8.1f}   ({(reference - sc.mean) / reference:+.1%})   {describe(sc.config)}")
    print(f"  ganancia del afinado vs mejor default: {report.gain_vs_best_baseline():+.2%}; gana en {report.wins_per_instance()}/{len(test)} instancias")

    payload = {
        "catalog": catalog, "generated_components": gen_names,
        "settings": {"trials": args.trials, "budget": args.budget, "train": len(train), "test": len(test),
                     "items": args.items, "periods": args.periods, "seed": args.seed, "seeds_test": args.seeds},
        "tuning": result.to_dict(), "test": report.to_dict(),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{catalog}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--budget", type=float, default=5.0, help="segundos por corrida (tuning y test)")
    ap.add_argument("--train", type=int, default=3)
    ap.add_argument("--test", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=3, help="semillas por instancia en test")
    ap.add_argument("--items", type=int, default=10)
    ap.add_argument("--periods", type=int, default=15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--catalog", choices=["handwritten", "all", "both"], default="both")
    ap.add_argument("--generated", default="generated/clsp")
    ap.add_argument("--out", default="tuning_out")
    ap.add_argument("--irace", default=None, help="directorio donde escribir un escenario irace (opcional)")
    args = ap.parse_args()

    train = make_instances(args.train, args.items, args.periods, 100 + args.seed * 1000)
    test = make_instances(args.test, args.items, args.periods, 500 + args.seed * 1000)
    out_dir = Path(args.out)
    catalogs = ["handwritten", "all"] if args.catalog == "both" else [args.catalog]
    results = {c: run_experiment(c, args, train, test, out_dir) for c in catalogs}

    if len(results) == 2:
        h, a = results["handwritten"]["test"], results["all"]["test"]
        diff = (h["tuned"]["mean"] - a["tuned"]["mean"]) / h["tuned"]["mean"]
        print(f"\n=== ¿ayuda o diluye? test afinado: a mano {h['tuned']['mean']:.1f} vs con LLM {a['tuned']['mean']:.1f} ({diff:+.2%}) ===")
        (out_dir / "comparison.json").write_text(json.dumps({
            "handwritten_tuned_test": h["tuned"]["mean"], "all_tuned_test": a["tuned"]["mean"],
            "relative_gain_from_llm_catalog": diff,
            "handwritten_best": h["tuned"]["summary"], "all_best": a["tuned"]["summary"],
        }, indent=2, ensure_ascii=False))

    if args.irace:
        from tuning.irace_scenario import write_irace_scenario

        inst_dir = Path(args.irace) / "instances"
        inst_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for k, inst in enumerate(train):
            p = inst_dir / f"train_{k}.txt"
            inst.save(str(p))
            paths.append(p)
        assembler, _ = make_assembler(catalogs[-1], args.generated)
        scenario = write_irace_scenario(assembler.config_space(), args.irace, paths, args.budget,
                                        max_experiments=args.trials * len(train),
                                        generated_dir=args.generated if catalogs[-1] == "all" else None)
        print(f"\nEscenario irace escrito en {scenario} (correr: irace --scenario {scenario})")


if __name__ == "__main__":
    main()
