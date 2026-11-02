"""Configuraciones del flow shop de permutación (flowtime total) en las 120 instancias de Taillard, con el protocolo de la
literatura: n·m/2·t milisegundos por instancia (t = 60, 90, ...). Gap (RPD) contra la mejor conocida
(`examples/flowshop/taillard/best_known.json`; con `--problem flowshop_cmax`, makespan y `examples/flowshop_cmax/best_known.json`);
un gap negativo es una mejor solución nueva.

    python -m scripts.pfsp_eval results/tune_runNN --generated generated/flowshop_native --native --t 60 --seeds 1 \\
        --out results/pfsp_runNN.json [--extra nombre='{"skeleton": ...}'] [--classes 50_10 100_20]
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random
from statistics import mean

TAILLARD = Path(__file__).resolve().parent.parent / "examples" / "flowshop" / "taillard"
BEST_KNOWN = {"flowshop": TAILLARD / "best_known.json",
              "flowshop_cmax": TAILLARD.parent.parent / "flowshop_cmax" / "best_known.json"}
CLASSES = ["20_5", "20_10", "20_20", "50_5", "50_10", "50_20", "100_5", "100_10", "100_20", "200_10", "200_20", "500_20"]


def best_known(problem: str = "flowshop") -> dict[str, float]:
    return {k: v for k, v in json.loads(BEST_KNOWN[problem].read_text()).items() if not k.startswith("_")}


def _pack(problem: str):
    import importlib

    return importlib.import_module(f"examples.{problem}.pack").PACK


def budget(name: str, t: float) -> float:
    _, n, m, _ = name.split("_") if name.count("_") == 3 else ("", *name[3:].split("_"))
    return int(n) * int(m) / 2 * t / 1000.0


def _run(args):
    label, config, name, seed, t, native, catalog, generated, problem = args
    from examples.flowshop.instance import PFSPInstance
    from tuning.cli import make_assembler

    PACK = _pack(problem)
    assembler, _ = make_assembler(PACK, catalog, generated, native=native)
    inst = PFSPInstance.load(str(TAILLARD / f"{name}.txt"))
    res = assembler.assemble(config)(inst, Random(seed), budget(name, t))
    P = PACK.problem_factory(inst)
    return {"config": label, "instance": name, "seed": seed, "flowtime": P.objective(res.best_solution),
            "feasible": P.is_feasible(res.best_solution), "solution": list(res.best_solution[0]), "iterations": res.iterations}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--catalog", default="generated")
    ap.add_argument("--generated", default=None)
    ap.add_argument("--native", action="store_true")
    ap.add_argument("--t", type=float, default=60.0)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--classes", nargs="*", default=CLASSES)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--problem", choices=sorted(BEST_KNOWN), default="flowshop", help="flowshop (flowtime) o flowshop_cmax")
    ap.add_argument("--out")
    args = ap.parse_args()

    from scripts.tuning_replicas import load_replicas
    from tuning.cli import make_assembler
    PACK = _pack(args.problem)
    make_assembler(PACK, args.catalog, args.generated, native=args.native)  # compila una vez antes de repartir
    configs = {}
    for run in args.runs:
        for rep, path in load_replicas(Path(run)):
            payload = json.loads((path / f"{args.catalog}.json").read_text())
            configs[f"{Path(run).name}/{rep}"] = (payload["test"]["tuned"]["config"], payload["test"]["tuned"]["summary"])
    for item in args.extra:
        name, cfg = item.split("=", 1)
        configs[name] = (json.loads(cfg), "extra")
    bk = best_known(args.problem)
    names = [f"tai{c}_{k}" for c in args.classes for k in range(10)]
    jobs = [(label, cfg, n, s, args.t, args.native, args.catalog, args.generated, args.problem) for label, (cfg, _) in configs.items()
            for n in names for s in range(args.seeds)]
    jobs.sort(key=lambda j: -budget(j[2], args.t))  # las largas primero
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_run, jobs))
    rpd = lambda r: 100 * (r["flowtime"] - bk[r["instance"]]) / bk[r["instance"]]  # noqa: E731
    print(f"RPD contra la mejor conocida; n·m/2·{args.t:g} ms; {args.seeds} semilla(s)\n")
    print(f"{'clase':<8}" + "".join(f"{label[-22:]:>24}" for label in configs))
    for c in args.classes:
        cells = [mean(rpd(r) for r in rows if r["config"] == label and r["instance"].startswith(f"tai{c}_")) for label in configs]
        print(f"{c:<8}" + "".join(f"{v:>23.2f}%" for v in cells))
    print(f"{'media':<8}" + "".join(f"{mean(rpd(r) for r in rows if r['config'] == label):>23.2f}%" for label in configs))
    new = [(r["instance"], r["flowtime"], bk[r["instance"]], r["config"]) for r in rows if r["feasible"] and r["flowtime"] < bk[r["instance"]]]
    print(f"\nmejores soluciones nuevas: {len({n for n, *_ in new})}" + "".join(f"\n  {n}: {f:.0f} < {b:.0f} ({c})" for n, f, b, c in sorted(new)))
    if args.out:
        Path(args.out).write_text(json.dumps({"t": args.t, "seeds": args.seeds, "best_known": bk,
                                              "configs": {k: v[1] for k, v in configs.items()}, "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
