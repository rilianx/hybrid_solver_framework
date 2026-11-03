"""Configuraciones del CLSP en las instancias de Trigeiro, Thomas y McClain (1989) de strIPlib
(`examples/lotsizing/trigeiro/`): gap contra la mejor referencia por instancia (óptimo o mejor solución de CBC en
`cbc.json`, y para las G además la tabla 9 de Degraeve y Jans en `reference.json`).

    python -m scripts.clsp_trigeiro_eval results/tune_run71 --generated generated/clsp_native --native --budget 60 \\
        --out results/clsp_trigeiro_run71.json [--extra nombre='{"skeleton": ...}'] [--only G]
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random
from statistics import mean

DIR = Path(__file__).resolve().parent.parent / "examples" / "lotsizing" / "trigeiro"


def references() -> dict[str, float]:
    """La mejor solución conocida por instancia: CBC (`cbc.json`) y, en las G, las de la tabla 9 de Degraeve y Jans."""
    best: dict[str, float] = {}
    if (DIR / "cbc.json").exists():
        for k, v in json.loads((DIR / "cbc.json").read_text()).items():
            if not k.startswith("_") and v.get("ub") is not None:
                best[k] = v["ub"]
    for k, v in json.loads((DIR / "reference.json").read_text()).items():
        if k.startswith("_"):
            continue
        for key in ("BW_IP", "BP_IP"):
            if key in v:
                best[k] = min(best.get(k, float("inf")), v[key])
    return best


def _run(args):
    label, config, name, seed, budget, native, catalog, generated = args
    from examples.lotsizing.instance import CLSPInstance
    from examples.lotsizing.pack import PACK
    from tuning.cli import make_assembler

    assembler, _ = make_assembler(PACK, catalog, generated, native=native)
    inst = CLSPInstance.load(str(DIR / f"{name}.txt"))
    res = assembler.assemble(config)(inst, Random(seed), budget)
    P = PACK.problem_factory(inst)
    return {"config": label, "instance": name, "seed": seed, "cost": P.objective(res.best_solution),
            "feasible": P.is_feasible(res.best_solution), "iterations": res.iterations}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--catalog", default="generated")
    ap.add_argument("--generated", default=None)
    ap.add_argument("--native", action="store_true")
    ap.add_argument("--budget", type=float, default=60.0, help="segundos por corrida")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--only", default="", help="prefijo de las instancias (F o G); vacío = todas")
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out")
    args = ap.parse_args()

    from examples.lotsizing.pack import PACK
    from scripts.tuning_replicas import load_replicas
    from tuning.cli import make_assembler

    make_assembler(PACK, args.catalog, args.generated, native=args.native)  # compila una vez
    configs = {}
    for run in args.runs:
        for rep, path in load_replicas(Path(run)):
            payload = json.loads((path / f"{args.catalog}.json").read_text())
            configs[f"{Path(run).name}/{rep}"] = payload["test"]["tuned"]["config"]
    for item in args.extra:
        name, cfg = item.split("=", 1)
        configs[name] = json.loads(cfg)
    ref = references()
    names = sorted(p.stem for p in DIR.glob(f"{args.only}*.txt"))
    jobs = [(label, cfg, n, s, args.budget, args.native, args.catalog, args.generated)
            for label, cfg in configs.items() for n in names for s in range(args.seeds)]
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_run, jobs))
    gap = lambda r: 100 * (r["cost"] - ref[r["instance"]]) / ref[r["instance"]]  # noqa: E731
    print(f"gap contra la mejor conocida; {args.budget:g} s por corrida; {args.seeds} semilla(s)\n")
    groups = {"F": [n for n in names if n.startswith("F")], **{n: [n] for n in names if n.startswith("G")}}
    print(f"{'grupo':<8}" + "".join(f"{label[-22:]:>24}" for label in configs))
    for g, members in groups.items():
        if not members or not all(m in ref for m in members):
            continue
        cells = [mean(gap(r) for r in rows if r["config"] == label and r["instance"] in members) for label in configs]
        print(f"{g:<8}" + "".join(f"{v:>23.2f}%" for v in cells))
    infeas = [(r["config"], r["instance"]) for r in rows if not r["feasible"]]
    print(f"\ninfactibles: {len(infeas)}" + "".join(f"\n  {c} {n}" for c, n in infeas[:20]))
    new = [(r["instance"], r["cost"], ref[r["instance"]], r["config"]) for r in rows
           if r["feasible"] and r["instance"] in ref and r["cost"] < ref[r["instance"]] - 1e-6]
    print(f"mejores que la referencia: {len(new)}" + "".join(f"\n  {n}: {c:.0f} < {b:.0f} ({l})" for n, c, b, l in new))
    if args.out:
        Path(args.out).write_text(json.dumps({"budget": args.budget, "seeds": args.seeds, "reference": ref,
                                              "configs": configs, "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
