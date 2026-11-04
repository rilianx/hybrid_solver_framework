"""Configuración automática del catálogo generado de un problema (§8). Genérico: recibe un `ProblemPack`
(`python -m examples.flowshop.tune …`). El catálogo son los componentes C++ que escribió el LLM en el workspace
(`--generated`, por defecto `generated/<problema>_native`; `llm.native_generator`) más las partidas trivial y al azar y,
si el problema tiene vista MIP, las destrucciones genéricas de HYB (`core.packs`); las corridas son en C++.

1. irace (`--tuner irace`) o la configuración en tres etapas (`--tuner staged`, `tuning.staged`) sobre el espacio de
   esqueletos, componentes y parámetros. El costo de una corrida es `costo / costo de la partida trivial` por
   instancia (`--objective ratio`), así ninguna instancia domina por escala; `--objective raw` usa el costo en bruto.
   Presupuesto: `--trials × --train` experimentos.
2. La mejor configuración se evalúa en instancias de TEST (no vistas), con `--seeds` semillas, contra el default de
   cada esqueleto (o, con `--skeletons` y `--baselines variants`, contra una variante por componente de cada slot).
3. Se guarda `tuning_out/generated.json` y se imprime la comparación.

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

CATALOG = "generated"  # nombre de la salida (`tuning_out/generated.json`) que leen los resúmenes y scripts/bench_eval


def make_assembler(pack: ProblemPack, generated_dir: str | None = None, skeletons: list[str] | None = None,
                   scale_budget: bool = False) -> tuple[Assembler, list[str]]:
    """El ensamblador del catálogo generado del workspace, en C++ (`core.native_runner`), y los nombres de los
    componentes generados."""
    from dataclasses import replace

    from core.native_runner import NATIVE_SKELETONS, NativeAssembler
    from llm.native_generator import load_native_catalog
    from native.check import NATIVE_SKELETONS_FOR_SLOT
    from native.generated import factory

    mod, model_of, entries = load_native_catalog(pack, generated_dir or pack.default_workspace)
    base = [({"name": n, "slot": "constructor", "compatible_skeletons": NATIVE_SKELETONS_FOR_SLOT["constructor"],
              "params": {}}, factory(mod, model_of, "constructor", n)) for n in ("trivial", "random")]
    mip = [(c, f) for c, f in pack.handwritten if c["slot"] == "destruction"]  # el sub-MIP de HYB es de Python
    registry = build_registry(replace(pack, handwritten=base + entries + mip))
    names = [s for s in (skeletons or NATIVE_SKELETONS) if s in NATIVE_SKELETONS]
    assembler = NativeAssembler(problem_factory=pack.problem_factory, registry=registry,
                                skeletons={k: SKELETONS[k] for k in names}, native=mod, model_of=model_of)
    if scale_budget:
        if pack.budget_scale is None:
            raise SystemExit(f"--scale-budget: el problema {pack.name} no define budget_scale")
        assembler.budget_scale = pack.budget_scale
    return assembler, [c["name"] for c, _ in entries]


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


def run_experiment(pack: ProblemPack, args, train, test, out_dir: Path):
    catalog = CATALOG
    assembler, gen_names = make_assembler(pack, args.generated, skeletons=args.skeletons, scale_budget=args.scale_budget)
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
                     "generated": args.generated, "tuner": args.tuner},
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
                                    generated_dir=args.generated, problem_module=pack.module, skeletons=args.skeletons,
                                    objective=args.objective, scale_budget=args.scale_budget)
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
    ap.add_argument("--skeletons", nargs="*", choices=sorted(SKELETONS), default=None,
                    help="restringe el espacio a estos esqueletos (baselines de test: uno por componente)")
    ap.add_argument("--objective", choices=["ratio", "raw"], default="ratio",
                    help="costo de un trial: media de costo/partida trivial por instancia (ratio) o costo medio (raw)")
    ap.add_argument("--ref-time", type=float, default=0.0,
                    help="segundos del MIP completo por instancia de test como referencia del gap (0 = sin MIP)")
    ap.add_argument("--generated", default=pack.default_workspace, help="workspace de los componentes generados")
    ap.add_argument("--out", default="tuning_out")
    ap.add_argument("--tuner", choices=["irace", "staged"], default="irace",
                    help="irace o la configuración en tres etapas (tuning.staged); los dos necesitan R con el paquete "
                         "irace (Ubuntu: apt install r-cran-irace)")
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
    payload, report, penalty = run_experiment(pack, args, train, test, out_dir)

    # mejor conocido por instancia de test: todas las corridas (+ MIP completo)
    mip_refs = None
    if args.ref_time > 0:
        print(f"\nReferencia: MIP completo, {args.ref_time:.0f} s por instancia de test")
        mip_refs = [pack.mip_reference(i, args.ref_time) for i in test]
        print("  " + ", ".join("—" if r is None else f"{r:.1f}" for r in mip_refs))
    report.best_known = best_known_costs(report.scores(), mip_refs, penalty)
    print_test(CATALOG, report, mean(pack.baseline_cost(i) for i in test), len(test))
    payload["test"] = report.to_dict()
    payload["test"]["mip_reference"] = mip_refs
    (out_dir / f"{CATALOG}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.irace:
        from tuning.irace_scenario import write_irace_scenario

        inst_dir = Path(args.irace) / "instances"
        inst_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for k, inst in enumerate(train):
            p = inst_dir / f"train_{k}.txt"
            inst.save(str(p))
            paths.append(p)
        assembler, _ = make_assembler(pack, args.generated, skeletons=args.skeletons)
        scenario = write_irace_scenario(assembler.config_space(), args.irace, paths, args.budget,
                                        max_experiments=args.trials * len(train), generated_dir=args.generated,
                                        problem_module=pack.module, skeletons=args.skeletons, objective=args.objective)
        print(f"\nEscenario irace escrito en {scenario} (correr: irace --scenario {scenario})")

