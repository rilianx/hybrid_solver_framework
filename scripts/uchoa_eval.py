"""Las configuraciones elegidas por corridas de tuning del CVRP, en las instancias X de Uchoa et al. (2017), con el
gap contra la mejor solución conocida (CVRPLIB, `examples/cvrp/uchoa/`). Como `scripts/taillard_eval.py`.

    python -m scripts.uchoa_eval results/tune_run65 --catalog generated --generated generated/cvrp_native \\
        --native --seeds 3 --budget 30 --out results/uchoa_run65.json

`--extra nombre='{"skeleton": ...}'` agrega una configuración más (p.ej. una sin afinar como referencia).
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random
from statistics import mean

UCHOA = Path(__file__).resolve().parent.parent / "examples" / "cvrp" / "uchoa"


def best_known() -> dict[str, float]:
    return {k: v for k, v in json.loads((UCHOA / "best_known.json").read_text()).items() if not k.startswith("_")}


def _run(args):
    label, config, name, seed, budget, native, catalog, generated, pack_module = args
    import importlib

    from examples.cvrp.instance import CVRPInstance
    from tuning.cli import make_assembler

    PACK = importlib.import_module(pack_module).PACK
    assembler, _ = make_assembler(PACK, catalog, generated, native=native)
    inst = CVRPInstance.load(str(UCHOA / f"{name}.vrp"))
    res = assembler.assemble(config)(inst, Random(seed), budget)
    P = PACK.problem_factory(inst)
    return {"config": label, "instance": name, "seed": seed, "cost": P.objective(res.best_solution),
            "feasible": P.is_feasible(res.best_solution), "iterations": res.iterations}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", help="directorios results/tune_runNN (una configuración por réplica)")
    ap.add_argument("--catalog", default="generated")
    ap.add_argument("--instances", nargs="*", default=None, help="por defecto, todas las de examples/cvrp/uchoa")
    ap.add_argument("--budget", type=float, default=30.0)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--native", action="store_true")
    ap.add_argument("--generated", default=None)
    ap.add_argument("--extra", nargs="*", default=[], help="nombre=JSON de una configuración adicional")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--pack", default="examples.cvrp.pack", help="módulo del pack (p.ej. examples.cvrp_gen.pack, modelo C++ generado)")
    ap.add_argument("--out")
    args = ap.parse_args()

    from scripts.tuning_replicas import load_replicas

    configs = {}
    for run in args.runs:
        for rep, path in load_replicas(Path(run)):
            payload = json.loads((path / f"{args.catalog}.json").read_text())
            configs[f"{Path(run).name}/{rep}"] = (payload["test"]["tuned"]["config"], payload["test"]["tuned"]["summary"])
    for item in args.extra:
        name, cfg = item.split("=", 1)
        configs[name] = (json.loads(cfg), "extra")
    bk = best_known()
    names = args.instances or sorted(bk, key=lambda n: int(n.split("-n")[1].split("-")[0]))
    jobs = [(label, cfg, name, seed, args.budget, args.native, args.catalog, args.generated, args.pack) for label, (cfg, _) in configs.items()
            for name in names for seed in range(args.seeds)]
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_run, jobs))
    gap = lambda r: (r["cost"] - bk[r["instance"]]) / bk[r["instance"]]  # noqa: E731
    print(f"gap contra la mejor solución conocida; {args.budget:g} s por corrida, {args.seeds} semilla(s), {len(names)} instancias\n")
    for label, (_, summary) in configs.items():
        sel = [r for r in rows if r["config"] == label]
        best = mean(min(gap(r) for r in sel if r["instance"] == n) for n in names)
        bad = sum(not r["feasible"] for r in sel)
        print(f"{label:<22} {mean(gap(r) for r in sel):>7.2%}  (mejor de {args.seeds}: {best:.2%})   {summary}"
              + (f"  ({bad} INFACTIBLES)" if bad else ""))
    if args.out:
        Path(args.out).write_text(json.dumps({"budget": args.budget, "seeds": args.seeds, "best_known": bk,
                                              "configs": {k: v[1] for k, v in configs.items()}, "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
