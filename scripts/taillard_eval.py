"""Las configuraciones elegidas por corridas de tuning, en las instancias de Taillard (1993) del job shop,
con el gap contra el óptimo o la mejor cota superior publicada (JSPLIB, `examples/jobshop/taillard/`).

    python -m scripts.taillard_eval results/tune_run52 results/tune_run53 --budget 30 --native --out ta.json

Cada réplica de cada corrida es una configuración; se corre en cada instancia con `--seeds` semillas
(en paralelo, `--workers` procesos de un hilo cada uno).
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from random import Random
from statistics import mean

TAILLARD = Path(__file__).resolve().parent.parent / "examples" / "jobshop" / "taillard"


def best_known() -> dict[str, int]:
    return {k: v for k, v in json.loads((TAILLARD / "best_known.json").read_text()).items() if not k.startswith("_")}


def _run(args):
    label, config, name, seed, budget, native, catalog, generated = args
    from examples.jobshop.instance import JSSPInstance
    from examples.jobshop.pack import PACK
    from tuning.cli import make_assembler

    assembler, _ = make_assembler(PACK, catalog, generated, native=native)
    inst = JSSPInstance.load(str(TAILLARD / f"{name}.txt"))
    res = assembler.assemble(config)(inst, Random(seed), budget)
    P = PACK.problem_factory(inst)
    return {"config": label, "instance": name, "seed": seed, "makespan": P.objective(res.best_solution),
            "feasible": P.is_feasible(res.best_solution), "iterations": res.iterations}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="directorios results/tune_runNN (una configuración por réplica)")
    ap.add_argument("--catalog", default="handwritten")
    ap.add_argument("--instances", nargs="*", default=[f"ta{i:02d}" for i in range(1, 21)])
    ap.add_argument("--budget", type=float, default=30.0)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--native", action="store_true")
    ap.add_argument("--generated", default=None, help="workspace del catálogo generado (con --catalog generated)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out")
    args = ap.parse_args()

    from scripts.tuning_replicas import load_replicas

    configs = {}
    for run in args.runs:
        for rep, path in load_replicas(Path(run)):
            payload = json.loads((path / f"{args.catalog}.json").read_text())
            configs[f"{Path(run).name}/{rep}"] = (payload["test"]["tuned"]["config"], payload["test"]["tuned"]["summary"])
    bk = best_known()
    jobs = [(label, cfg, name, seed, args.budget, args.native, args.catalog, args.generated) for label, (cfg, _) in configs.items()
            for name in args.instances for seed in range(args.seeds)]
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_run, jobs))
    print(f"gap contra el óptimo o la mejor cota superior publicada; {args.budget:g} s por corrida, {args.seeds} semilla(s)\n")
    groups = {"ta01-10 (15×15)": [f"ta{i:02d}" for i in range(1, 11)], "ta11-20 (20×15)": [f"ta{i:02d}" for i in range(11, 21)]}
    print(f"{'configuración':<22}" + "".join(f"{g:>18}" for g in groups) + "   elegida")
    for label, (_, summary) in configs.items():
        cells = []
        for names in groups.values():
            sel = [r for r in rows if r["config"] == label and r["instance"] in names]
            cells.append(f"{mean((r['makespan'] - bk[r['instance']]) / bk[r['instance']] for r in sel):>17.2%}" if sel else f"{'—':>17}")
        bad = sum(not r["feasible"] for r in rows if r["config"] == label)
        print(f"{label:<22}" + " ".join(cells) + f"   {summary}" + (f"  ({bad} INFACTIBLES)" if bad else ""))
    if args.out:
        Path(args.out).write_text(json.dumps({"budget": args.budget, "seeds": args.seeds, "best_known": bk,
                                              "configs": {k: v[1] for k, v in configs.items()}, "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
