"""Tuning con Optuna sobre el catálogo de un problema (§8) y la pregunta de §10: ¿el catálogo
ampliado con componentes generados por LLM **ayuda o diluye**? Genérico: recibe un
`ProblemPack` (`python -m examples.lotsizing.tune …`, `python -m examples.cvrp.tune …`).

Para cada catálogo (`handwritten` = solo componentes a mano, `all` = + generados,
`generated` = solo generados; `--catalog both` corre los dos primeros y `three` los tres):
1. Optuna (TPE) sobre el espacio completo, con los defaults de cada esqueleto encolados
   como primeros trials. El costo de un trial es la media, por instancia de
   entrenamiento, de `costo / costo de la partida trivial` (`--objective ratio`): así
   ninguna instancia domina por escala. `--objective raw` usa el costo medio en bruto.
   Con `--reeval-top k`, selección final por re-evaluación con más semillas.
2. La mejor configuración se evalúa en instancias de TEST (no vistas), con 3 semillas,
   contra el default de cada esqueleto (o, con `--skeletons`, contra una variante por
   componente de cada slot).
3. Se guarda `tuning_out/<catalog>.json` y se imprime la comparación.

En test, cada configuración se resume como **gap relativo por instancia** contra la mejor
solución conocida (el mínimo entre todas las corridas y, con `--ref-time S`, el MIP
completo con S segundos), y el afinado se compara con el mejor default con un IC95.

Con `--irace DIR` además escribe un escenario irace listo para correr afuera.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from core.assembler import SKELETONS, Assembler, describe
from core.problem_pack import ProblemPack
from llm.catalog import build_registry, load_generated

from .evaluation import best_known_costs, evaluate_on_test, one_slot_baselines
from .optuna_tuner import tune_with_optuna


def make_assembler(pack: ProblemPack, catalog: str, generated_dir: str | None = None, verbose: bool = False,
                   skeletons: list[str] | None = None) -> tuple[Assembler, list[str]]:
    generated = load_generated(pack, generated_dir, verbose=verbose) if catalog in ("all", "generated") else []
    registry = build_registry(pack, generated, handwritten=catalog != "generated")
    sks = {k: SKELETONS[k] for k in skeletons} if skeletons else dict(SKELETONS)
    return Assembler(problem_factory=pack.problem_factory, registry=registry, skeletons=sks), [c.name for c in generated]


def run_experiment(pack: ProblemPack, catalog: str, args, train, test, out_dir: Path):
    assembler, gen_names = make_assembler(pack, catalog, args.generated, verbose=True, skeletons=args.skeletons)
    space = assembler.config_space()
    n_gen_in_space = sum(1 for n in space.nodes if n.type == "cat" for v in n.values if v in gen_names)
    print(f"\n=== catálogo `{catalog}`: {len(space.nodes)} parámetros, {n_gen_in_space} opciones generadas por LLM ===")

    def on_trial(t):
        mark = "*" if t.enqueued else " "
        print(f"  trial {t.number:>3}{mark} {t.cost:>12.4f}  {t.summary}")

    normalizers = [pack.baseline_cost(i) for i in train] if args.objective == "ratio" else None
    result = tune_with_optuna(assembler, train, args.budget, args.trials, seed=args.tuner_seed, space=space,
                              on_trial=on_trial, normalizers=normalizers,
                              reeval_top=args.reeval_top, reeval_seeds=args.reeval_seeds)
    for r in result.reevaluated:
        print(f"  re-evaluado #{r['number']:>3}{'*' if r['enqueued'] else ' '} media {r['mean']:.4f} "
              f"({', '.join(f'{c:.4f}' for c in r['costs'])})  {r['summary']}")
    print(f"  mejor en train: {result.best_cost:.4f}  {describe(result.best_config)}  ({result.seconds:.0f}s, {result.n_failed} fallidas)")

    reference = mean(pack.baseline_cost(i) for i in test)
    baselines = one_slot_baselines(assembler) if args.skeletons else None
    report = evaluate_on_test(assembler, result.best_config, test, args.budget, seeds=tuple(range(args.seeds)),
                              baselines=baselines, reference=reference)
    payload = {
        "catalog": catalog, "generated_components": gen_names,
        "settings": {"trials": args.trials, "budget": args.budget, "train": len(train), "test": len(test),
                     "problem": pack.name, "size": args.size, "seed": args.seed, "tuner_seed": args.tuner_seed, "seeds_test": args.seeds,
                     "objective": args.objective, "skeletons": args.skeletons or "all", "ref_time": args.ref_time,
                     "reeval_top": args.reeval_top, "reeval_seeds": args.reeval_seeds},
        "tuning": result.to_dict(),
    }
    return payload, report, assembler.penalty_cost


def print_test(catalog: str, report, reference: float, n_test: int) -> None:
    bk = report.best_known
    print(f"\n=== TEST `{catalog}` (partida trivial sin búsqueda = {reference:.1f}; gap vs mejor conocido por instancia) ===")
    rows = [("tuned", report.tuned)] + [(b.label, b) for b in sorted(report.baselines, key=lambda s: s.mean_gap(bk))]
    for label, sc in rows:
        print(f"    {label:<48} gap {sc.mean_gap(bk):>7.2%}   {sc.mean:>12.1f} ± {sc.std:>8.1f}   "
              f"({(reference - sc.mean) / reference:+.1%} vs partida)   {describe(sc.config)}")
    print(f"  ganancia del afinado vs mejor default: {report.gain_vs_best_baseline():+.2%}; "
          f"gana en {report.wins_per_instance()}/{n_test} instancias")
    pc = report.to_dict()["tuned_vs_best_baseline"]
    print(f"  afinado vs {pc['b']}: gap {pc['mean_diff']:+.2%} a favor del afinado, IC95 [{pc['ci95'][0]:+.2%}, {pc['ci95'][1]:+.2%}]"
          f"{'' if pc['significant'] else ' (no se distingue del ruido)'}")


def main(pack: ProblemPack, argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog=f"python -m {pack.module}.tune")
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--budget", type=float, default=5.0, help="segundos por corrida (tuning y test)")
    ap.add_argument("--train", type=int, default=3)
    ap.add_argument("--test", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=3, help="semillas por instancia en test")
    ap.add_argument("--size", default=pack.default_size, help=f"tamaño de las instancias (default {pack.default_size})")
    ap.add_argument("--seed", type=int, default=0, help="semilla de las instancias (y del tuner si no se da --tuner-seed)")
    ap.add_argument("--tuner-seed", type=int, default=None,
                    help="semilla del tuner y de las corridas de train, sin cambiar las instancias (réplicas del tuning)")
    ap.add_argument("--catalog", choices=["handwritten", "all", "generated", "both", "three"], default="both")
    ap.add_argument("--skeletons", nargs="*", choices=sorted(SKELETONS), default=None,
                    help="restringe el espacio a estos esqueletos (baselines de test: uno por componente)")
    ap.add_argument("--objective", choices=["ratio", "raw"], default="ratio",
                    help="costo de un trial: media de costo/partida trivial por instancia (ratio) o costo medio (raw)")
    ap.add_argument("--ref-time", type=float, default=0.0,
                    help="segundos del MIP completo por instancia de test como referencia del gap (0 = sin MIP)")
    ap.add_argument("--reeval-top", type=int, default=0,
                    help="selección final: re-evaluar en train los k mejores trials (y el mejor default) con más semillas")
    ap.add_argument("--reeval-seeds", type=int, default=2, help="semillas extra por configuración re-evaluada")
    ap.add_argument("--generated", default=pack.default_workspace)
    ap.add_argument("--out", default="tuning_out")
    ap.add_argument("--irace", default=None, help="directorio donde escribir un escenario irace (opcional)")
    args = ap.parse_args(argv)
    if args.tuner_seed is None:
        args.tuner_seed = args.seed

    size = pack.parse_size(args.size)
    train = pack.make_instances(args.train, 100 + args.seed * 1000, size)
    test = pack.make_instances(args.test, 500 + args.seed * 1000, size)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    catalogs = {"both": ["handwritten", "all"], "three": ["handwritten", "generated", "all"]}.get(args.catalog, [args.catalog])
    runs = {c: run_experiment(pack, c, args, train, test, out_dir) for c in catalogs}

    # mejor conocido por instancia de test: todas las corridas de ambos catálogos (+ MIP completo)
    mip_refs = None
    if args.ref_time > 0:
        print(f"\nReferencia: MIP completo, {args.ref_time:.0f} s por instancia de test")
        mip_refs = [pack.mip_reference(i, args.ref_time) for i in test]
        print("  " + ", ".join("—" if r is None else f"{r:.1f}" for r in mip_refs))
    penalty = next(iter(runs.values()))[2]
    best_known = best_known_costs([sc for _, rep, _ in runs.values() for sc in rep.scores()], mip_refs, penalty)
    reference = mean(pack.baseline_cost(i) for i in test)

    results = {}
    for c, (payload, report, _) in runs.items():
        report.best_known = best_known
        print_test(c, report, reference, len(test))
        payload["test"] = report.to_dict()
        payload["test"]["mip_reference"] = mip_refs
        (out_dir / f"{c}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        results[c] = payload

    if "handwritten" in results and len(results) > 1:
        h = results["handwritten"]["test"]
        comparison = {"handwritten_tuned_test": h["tuned"]["mean"], "handwritten_tuned_gap": h["tuned"]["mean_gap"],
                      "handwritten_best": h["tuned"]["summary"]}
        for other in ("all", "generated"):
            if other not in results:
                continue
            o = results[other]["test"]
            diff = (h["tuned"]["mean"] - o["tuned"]["mean"]) / h["tuned"]["mean"]
            label = "con LLM" if other == "all" else "solo LLM"
            print(f"\n=== a mano vs {label}: test afinado {h['tuned']['mean']:.1f} (gap {h['tuned']['mean_gap']:.2%}) "
                  f"vs {o['tuned']['mean']:.1f} (gap {o['tuned']['mean_gap']:.2%}) ({diff:+.2%}) ===")
            comparison.update({f"{other}_tuned_test": o["tuned"]["mean"], f"{other}_tuned_gap": o["tuned"]["mean_gap"],
                               f"{other}_best": o["tuned"]["summary"],
                               "relative_gain_from_llm_catalog" if other == "all" else "relative_gain_generated_only": diff})
        (out_dir / "comparison.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False))

    if args.irace:
        from tuning.irace_scenario import write_irace_scenario

        inst_dir = Path(args.irace) / "instances"
        inst_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for k, inst in enumerate(train):
            p = inst_dir / f"train_{k}.txt"
            inst.save(str(p))
            paths.append(p)
        assembler, _ = make_assembler(pack, catalogs[-1], args.generated, skeletons=args.skeletons)
        scenario = write_irace_scenario(assembler.config_space(), args.irace, paths, args.budget,
                                        max_experiments=args.trials * len(train),
                                        generated_dir=args.generated if catalogs[-1] != "handwritten" else None,
                                        problem_module=pack.module)
        print(f"\nEscenario irace escrito en {scenario} (correr: irace --scenario {scenario})")

