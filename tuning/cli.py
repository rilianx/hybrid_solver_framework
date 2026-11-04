"""Configuración automática sobre el catálogo de un problema (§8). Genérico: recibe un `ProblemPack`
(`python -m examples.flowshop.tune …`).

Catálogos: `handwritten` (componentes a mano del pack, en Python o, con `--native`, en C++), `generated`
(componentes C++ del LLM, `llm.native_generator`; siempre en C++) y `both` (los dos, por separado, y la comparación).

Para cada catálogo:
1. irace (`--tuner irace`) o la configuración en tres etapas (`--tuner staged`, `tuning.staged`) sobre el espacio de
   esqueletos, componentes y parámetros. El costo de una corrida es `costo / costo de la partida trivial` por
   instancia (`--objective ratio`), así ninguna instancia domina por escala; `--objective raw` usa el costo en bruto.
   Presupuesto: `--trials × --train` experimentos.
2. La mejor configuración se evalúa en instancias de TEST (no vistas), con `--seeds` semillas, contra el default de
   cada esqueleto (o, con `--skeletons` y `--baselines variants`, contra una variante por componente de cada slot).
3. Se guarda `tuning_out/<catalog>.json` y se imprime la comparación.

En test, cada configuración se resume como **gap relativo por instancia** contra la mejor solución conocida (el
mínimo entre todas las corridas y, con `--ref-time S`, el MIP completo con S segundos), y el afinado se compara con
el mejor default con un IC95. Con `--irace DIR` además escribe un escenario irace listo para correr afuera.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from core.assembler import SKELETONS, Assembler, describe
from core.problem_pack import ProblemPack
from core.catalog import build_registry

from .evaluation import best_known_costs, evaluate_on_test, one_slot_baselines

CATALOGS = ("handwritten", "generated")


def make_assembler(pack: ProblemPack, catalog: str, generated_dir: str | None = None, verbose: bool = False,
                   skeletons: list[str] | None = None, native: bool = False,
                   scale_budget: bool = False) -> tuple[Assembler, list[str]]:
    """Con `native=True` las configuraciones corren en C++ (`core.native_runner`): el catálogo se reduce a
    los componentes que existen en C++ y el espacio a los esqueletos nativos. El catálogo `generated` es siempre
    nativo. Devuelve el ensamblador y los nombres de los componentes generados."""
    if catalog not in CATALOGS:
        raise SystemExit(f"catálogo desconocido {catalog!r}: {', '.join(CATALOGS)}")
    native = native or catalog == "generated"
    mod = model_of = None
    gen_names: list[str] = []
    if native:
        from core.native_runner import NATIVE_SKELETONS, native_pack

        skeletons = [s for s in (skeletons or NATIVE_SKELETONS) if s in NATIVE_SKELETONS]
        if catalog == "handwritten":
            pack, mod = native_pack(pack)
            model_of = mod.model
            mod = mod.native
        elif catalog == "generated":  # componentes C++ del LLM (`llm.native_generator`) + las partidas de referencia
            from dataclasses import replace

            from llm.native_generator import load_native_catalog
            from native.check import NATIVE_SKELETONS_FOR_SLOT
            from native.generated import factory

            mod, model_of, entries = load_native_catalog(pack, generated_dir)
            gen_names = [c["name"] for c, _ in entries]
            base = [({"name": n, "slot": "constructor", "compatible_skeletons": NATIVE_SKELETONS_FOR_SLOT["constructor"],
                      "params": {}}, factory(mod, model_of, "constructor", n)) for n in ("trivial", "random")]
            # las destrucciones son de Python (el sub-MIP también): las del catálogo a mano, para HYB
            mip = [(c, f) for c, f in pack.handwritten if c["slot"] == "destruction"]
            pack = replace(pack, handwritten=base + entries + mip)
    registry = build_registry(pack)
    sks = {k: SKELETONS[k] for k in skeletons} if skeletons else dict(SKELETONS)
    if mod is not None:
        from core.native_runner import NativeAssembler

        assembler = NativeAssembler(problem_factory=pack.problem_factory, registry=registry, skeletons=sks,
                                    native=mod, model_of=model_of)
    else:
        assembler = Assembler(problem_factory=pack.problem_factory, registry=registry, skeletons=sks)
    if scale_budget:
        if pack.budget_scale is None:
            raise SystemExit(f"--scale-budget: el problema {pack.name} no define budget_scale")
        assembler.budget_scale = pack.budget_scale
    return assembler, gen_names


def mixed_instances(pack: ProblemPack, sizes: str, n: int, seed0: int) -> list:
    """`n` instancias repartidas entre los tamaños de `sizes` ("50x10" o "50x10,100x20,200x20"), en orden de tamaño;
    con un solo tamaño, lo mismo que `pack.make_instances`."""
    parts = [s.strip() for s in sizes.split(",") if s.strip()]
    if len(parts) == 1:
        return pack.make_instances(n, seed0, pack.parse_size(parts[0]))
    out = []
    for j, s in enumerate(parts):
        k = n // len(parts) + (1 if j < n % len(parts) else 0)
        out += pack.make_instances(k, seed0 + 10_000 * j, pack.parse_size(s))
    return out


def run_experiment(pack: ProblemPack, catalog: str, args, train, test, out_dir: Path):
    assembler, gen_names = make_assembler(pack, catalog, args.generated, verbose=True, skeletons=args.skeletons,
                                          native=args.native, scale_budget=args.scale_budget)
    space = assembler.config_space()
    n_gen_in_space = sum(1 for n in space.nodes if n.type == "cat" for v in n.values if v in gen_names)
    print(f"\n=== catálogo `{catalog}`: {len(space.nodes)} parámetros, {n_gen_in_space} opciones generadas por LLM ===")

    normalizers = [pack.baseline_cost(i) for i in train] if args.objective == "ratio" else None
    result = _run_irace(pack, catalog, args, assembler, train, normalizers, out_dir)
    print(f"  {args.tuner}: {result.experiments} experimentos en {result.seconds:.0f}s; élite: "
          + "; ".join(describe(e) for e in result.elites))
    print(f"  mejor en train: {result.best_cost:.4f}  {describe(result.best_config)}")

    reference = mean(pack.baseline_cost(i) for i in test)
    baselines = one_slot_baselines(assembler) if args.skeletons and args.baselines == "variants" else None
    report = evaluate_on_test(assembler, result.best_config, test, args.budget, seeds=tuple(range(args.seeds)),
                              baselines=baselines, reference=reference)
    payload = {
        "catalog": catalog, "generated_components": gen_names,
        "settings": {"trials": args.trials, "budget": args.budget, "train": len(train), "test": len(test),
                     "problem": pack.name, "size": args.size, "seed": args.seed, "tuner_seed": args.tuner_seed, "seeds_test": args.seeds,
                     "objective": args.objective, "skeletons": args.skeletons or "all", "ref_time": args.ref_time,
                     "native": args.native or catalog == "generated", "tuner": args.tuner},
        "tuning": result.to_dict(),
    }
    return payload, report, assembler.penalty_cost


def _run_irace(pack: ProblemPack, catalog: str, args, assembler, train, normalizers, out_dir: Path):
    """irace (o la configuración en etapas) sobre las instancias de entrenamiento, con trials × instancias de train
    experimentos."""
    from tuning.irace_runner import tune_with_irace
    from tuning.irace_scenario import write_irace_scenario

    root = out_dir / f"irace_{catalog}"
    inst_dir = root / "instances"
    inst_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for k, inst in enumerate(train):
        p = inst_dir / f"train_{k}.txt"
        inst.save(str(p))
        paths.append(p)
    experiments = args.trials * len(train)
    scenario = write_irace_scenario(assembler.config_space(), root, paths, args.budget, max_experiments=experiments,
                                    generated_dir=args.generated if catalog == "generated" else None,
                                    problem_module=pack.module, catalog=catalog, skeletons=args.skeletons,
                                    native=args.native or catalog == "generated", objective=args.objective,
                                    scale_budget=args.scale_budget)
    if args.tuner == "staged":
        from tuning.staged import run_staged

        return run_staged(assembler, scenario, paths, args.budget, experiments, seed=args.tuner_seed, top=args.stage_top,
                          parallel=args.irace_parallel, final_seeds=args.final_seeds, normalizers=normalizers,
                          skeletons=args.skeletons)
    return tune_with_irace(assembler, scenario, train, args.budget, experiments, seed=args.tuner_seed,
                           normalizers=normalizers, parallel=args.irace_parallel)


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
    ap.add_argument("--trials", type=int, default=30,
                    help="presupuesto del tuner: trials × instancias de train experimentos")
    ap.add_argument("--budget", type=float, default=5.0, help="segundos por corrida (tuning y test)")
    ap.add_argument("--train", type=int, default=3)
    ap.add_argument("--test", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=3, help="semillas por instancia en test")
    ap.add_argument("--size", default=pack.default_size, help=f"tamaño de las instancias (default {pack.default_size})")
    ap.add_argument("--seed", type=int, default=0, help="semilla de las instancias (y del tuner si no se da --tuner-seed)")
    ap.add_argument("--tuner-seed", type=int, default=None,
                    help="semilla del tuner y de las corridas de train, sin cambiar las instancias (réplicas del tuning)")
    ap.add_argument("--catalog", choices=["handwritten", "generated", "both"], default="generated",
                    help="componentes a mano, generados por el LLM en C++ (implica --native) o los dos por separado")
    ap.add_argument("--skeletons", nargs="*", choices=sorted(SKELETONS), default=None,
                    help="restringe el espacio a estos esqueletos (baselines de test: uno por componente)")
    ap.add_argument("--objective", choices=["ratio", "raw"], default="ratio",
                    help="costo de un trial: media de costo/partida trivial por instancia (ratio) o costo medio (raw)")
    ap.add_argument("--ref-time", type=float, default=0.0,
                    help="segundos del MIP completo por instancia de test como referencia del gap (0 = sin MIP)")
    ap.add_argument("--generated", default=pack.default_workspace)
    ap.add_argument("--out", default="tuning_out")
    ap.add_argument("--tuner", choices=["irace", "staged"], default="irace",
                    help="irace o la configuración en tres etapas (tuning.staged); los dos necesitan R con el paquete "
                         "irace (Ubuntu: apt install r-cran-irace)")
    ap.add_argument("--native", action="store_true",
                    help="correr las configuraciones en C++ (backend nativo del problema; SA, ILS, VNS, TS, PR y HYB)")
    ap.add_argument("--scale-budget", action="store_true",
                    help="presupuesto por instancia = --budget × el factor de tamaño del problema (budget_scale del pack)")
    ap.add_argument("--baselines", choices=["variants", "defaults"], default="variants",
                    help="baselines de test con --skeletons: una variante por componente (variants) o solo el default "
                         "de cada esqueleto (defaults, mucho más barato)")
    ap.add_argument("--stage-top", type=int, default=2, help="staged: estructuras que pasan de la etapa 1 a irace")
    ap.add_argument("--final-seeds", type=int, default=3, help="staged: semillas nuevas de la validación final")
    ap.add_argument("--irace-parallel", type=int, default=1,
                    help="experimentos de irace a la vez (los runners de GitHub tienen 4 núcleos)")
    ap.add_argument("--irace", default=None, help="directorio donde escribir un escenario irace (opcional)")
    args = ap.parse_args(argv)
    if args.tuner_seed is None:
        args.tuner_seed = args.seed

    train = mixed_instances(pack, args.size, args.train, 100 + args.seed * 1000)
    test = mixed_instances(pack, args.size, args.test, 500 + args.seed * 1000)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    catalogs = list(CATALOGS) if args.catalog == "both" else [args.catalog]
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

    if len(results) > 1:
        h, g = results["handwritten"]["test"], results["generated"]["test"]
        diff = (h["tuned"]["mean"] - g["tuned"]["mean"]) / h["tuned"]["mean"]
        print(f"\n=== a mano vs LLM: test afinado {h['tuned']['mean']:.1f} (gap {h['tuned']['mean_gap']:.2%}) "
              f"vs {g['tuned']['mean']:.1f} (gap {g['tuned']['mean_gap']:.2%}) ({diff:+.2%}) ===")
        comparison = {"handwritten_tuned_test": h["tuned"]["mean"], "handwritten_tuned_gap": h["tuned"]["mean_gap"],
                      "handwritten_best": h["tuned"]["summary"], "generated_tuned_test": g["tuned"]["mean"],
                      "generated_tuned_gap": g["tuned"]["mean_gap"], "generated_best": g["tuned"]["summary"],
                      "relative_gain_generated_only": diff}
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
        assembler, _ = make_assembler(pack, catalogs[-1], args.generated, skeletons=args.skeletons, native=args.native)
        scenario = write_irace_scenario(assembler.config_space(), args.irace, paths, args.budget,
                                        max_experiments=args.trials * len(train),
                                        generated_dir=args.generated if catalogs[-1] == "generated" else None,
                                        problem_module=pack.module, catalog=catalogs[-1], skeletons=args.skeletons,
                                        native=args.native or catalogs[-1] == "generated", objective=args.objective)
        print(f"\nEscenario irace escrito en {scenario} (correr: irace --scenario {scenario})")

