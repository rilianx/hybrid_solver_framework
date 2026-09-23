"""Tuning real sobre el CLSP (§8) y la pregunta de §10: ¿el catálogo ampliado con
componentes generados por LLM **ayuda o diluye**?

    python -m examples.lotsizing.tune --trials 30 --budget 5 --train 3 --test 3 --catalog both
    python -m examples.lotsizing.tune --skeletons SA ILS VNS --ref-time 60   # esqueleto fijo

Para cada catálogo (`handwritten` = solo componentes a mano, `all` = + generados,
`generated` = solo generados; `--catalog both` corre los dos primeros y `three` los tres):
1. Optuna (TPE) sobre el espacio completo, con los defaults de cada esqueleto
   encolados como primeros trials. El costo de un trial es la media, por instancia
   de entrenamiento, de `costo / lot-for-lot` (`--objective ratio`): así ninguna
   instancia domina por escala. `--objective raw` usa el costo medio en bruto.
2. La mejor configuración se evalúa en instancias de TEST (no vistas), con 3
   semillas, contra el default de cada esqueleto.
3. Se guarda `tuning_out/<catalog>.json` y se imprime la comparación.

En test, además del costo medio, cada configuración se resume como **gap relativo
por instancia** contra la mejor solución conocida de esa instancia: el mínimo entre
todas las corridas de test de ambos catálogos y, con `--ref-time S`, la solución del
MIP completo con S segundos.

Con `--skeletons` el espacio se restringe a esos esqueletos y los baselines de test
pasan a ser uno por componente de cada slot (los demás en su default): la
comparación en igualdad de condiciones entre componentes generados y de mano, que
con el espacio completo no se ve porque con presupuestos cortos siempre gana un
esqueleto matheurístico.

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

from core.assembler import SKELETONS, Assembler, describe
from tuning import best_known_costs, evaluate_on_test, one_slot_baselines, tune_with_optuna

from .catalog import build_registry, load_generated
from .components import LotForLotConstructor
from .problem_model import CLSPInstance, LotSizingModel


def make_instances(n: int, items: int, periods: int, seed0: int, utilization: float = 0.95, tbo: float = 3.0):
    return [CLSPInstance.trigeiro(items, periods, Random(seed0 + k), utilization=utilization, tbo=tbo) for k in range(n)]


def make_assembler(catalog: str, generated_dir: str, verbose: bool = False,
                   skeletons: list[str] | None = None) -> tuple[Assembler, list[str]]:
    generated = load_generated(generated_dir, verbose=verbose) if catalog in ("all", "generated") else []
    registry = build_registry(generated, handwritten=catalog != "generated")
    sks = {k: SKELETONS[k] for k in skeletons} if skeletons else dict(SKELETONS)
    return Assembler(problem_factory=LotSizingModel, registry=registry, skeletons=sks), [c.name for c in generated]


def lot_for_lot_cost(inst: CLSPInstance) -> float:
    return LotSizingModel(inst).objective(LotForLotConstructor().build(inst, Random(0)))


def mip_reference(inst: CLSPInstance, seconds: float) -> float | None:
    """Costo de la mejor solución que el MIP completo encuentra en `seconds` (None si ninguna factible)."""
    P = LotSizingModel(inst)
    model = P.build_mip(inst)
    x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=seconds)
    if x is None:
        return None
    sol = P.from_assignment(x)
    return P.objective(sol) if P.is_feasible(sol) else None


def run_experiment(catalog: str, args, train, test, out_dir: Path):
    assembler, gen_names = make_assembler(catalog, args.generated, verbose=True, skeletons=args.skeletons)
    space = assembler.config_space()
    n_gen_in_space = sum(1 for n in space.nodes if n.type == "cat" for v in n.values if v in gen_names)
    print(f"\n=== catálogo `{catalog}`: {len(space.nodes)} parámetros, {n_gen_in_space} opciones generadas por LLM ===")

    def on_trial(t):
        mark = "*" if t.enqueued else " "
        print(f"  trial {t.number:>3}{mark} {t.cost:>12.4f}  {t.summary}")

    normalizers = [lot_for_lot_cost(i) for i in train] if args.objective == "ratio" else None
    result = tune_with_optuna(assembler, train, args.budget, args.trials, seed=args.seed, space=space,
                              on_trial=on_trial, normalizers=normalizers)
    print(f"  mejor en train: {result.best_cost:.4f}  {describe(result.best_config)}  ({result.seconds:.0f}s, {result.n_failed} fallidas)")

    reference = mean(lot_for_lot_cost(i) for i in test)
    baselines = one_slot_baselines(assembler) if args.skeletons else None
    report = evaluate_on_test(assembler, result.best_config, test, args.budget, seeds=tuple(range(args.seeds)),
                              baselines=baselines, reference=reference)
    payload = {
        "catalog": catalog, "generated_components": gen_names,
        "settings": {"trials": args.trials, "budget": args.budget, "train": len(train), "test": len(test),
                     "items": args.items, "periods": args.periods, "seed": args.seed, "seeds_test": args.seeds,
                     "objective": args.objective, "skeletons": args.skeletons or "all", "ref_time": args.ref_time},
        "tuning": result.to_dict(),
    }
    return payload, report, assembler.penalty_cost


def print_test(catalog: str, report, reference: float, n_test: int) -> None:
    bk = report.best_known
    print(f"\n=== TEST `{catalog}` (lot-for-lot sin búsqueda = {reference:.1f}; gap vs mejor conocido por instancia) ===")
    rows = [("tuned", report.tuned)] + [(b.label, b) for b in sorted(report.baselines, key=lambda s: s.mean_gap(bk))]
    for label, sc in rows:
        print(f"    {label:<48} gap {sc.mean_gap(bk):>7.2%}   {sc.mean:>12.1f} ± {sc.std:>8.1f}   "
              f"({(reference - sc.mean) / reference:+.1%} vs lfl)   {describe(sc.config)}")
    print(f"  ganancia del afinado vs mejor default: {report.gain_vs_best_baseline():+.2%}; "
          f"gana en {report.wins_per_instance()}/{n_test} instancias")


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
    ap.add_argument("--catalog", choices=["handwritten", "all", "generated", "both", "three"], default="both")
    ap.add_argument("--skeletons", nargs="*", choices=sorted(SKELETONS), default=None,
                    help="restringe el espacio a estos esqueletos (baselines de test: uno por componente)")
    ap.add_argument("--objective", choices=["ratio", "raw"], default="ratio",
                    help="costo de un trial: media de costo/lot-for-lot por instancia (ratio) o costo medio (raw)")
    ap.add_argument("--ref-time", type=float, default=0.0,
                    help="segundos del MIP completo por instancia de test como referencia del gap (0 = sin MIP)")
    ap.add_argument("--generated", default="generated/clsp")
    ap.add_argument("--out", default="tuning_out")
    ap.add_argument("--irace", default=None, help="directorio donde escribir un escenario irace (opcional)")
    args = ap.parse_args()

    train = make_instances(args.train, args.items, args.periods, 100 + args.seed * 1000)
    test = make_instances(args.test, args.items, args.periods, 500 + args.seed * 1000)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    catalogs = {"both": ["handwritten", "all"], "three": ["handwritten", "generated", "all"]}.get(args.catalog, [args.catalog])
    runs = {c: run_experiment(c, args, train, test, out_dir) for c in catalogs}

    # mejor conocido por instancia de test: todas las corridas de ambos catálogos (+ MIP completo)
    mip_refs = None
    if args.ref_time > 0:
        print(f"\nReferencia: MIP completo, {args.ref_time:.0f} s por instancia de test")
        mip_refs = [mip_reference(i, args.ref_time) for i in test]
        print("  " + ", ".join("—" if r is None else f"{r:.1f}" for r in mip_refs))
    penalty = next(iter(runs.values()))[2]
    best_known = best_known_costs([sc for _, rep, _ in runs.values() for sc in rep.scores()], mip_refs, penalty)
    reference = mean(lot_for_lot_cost(i) for i in test)

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
        assembler, _ = make_assembler(catalogs[-1], args.generated, skeletons=args.skeletons)
        scenario = write_irace_scenario(assembler.config_space(), args.irace, paths, args.budget,
                                        max_experiments=args.trials * len(train),
                                        generated_dir=args.generated if catalogs[-1] != "handwritten" else None)
        print(f"\nEscenario irace escrito en {scenario} (correr: irace --scenario {scenario})")


if __name__ == "__main__":
    main()
