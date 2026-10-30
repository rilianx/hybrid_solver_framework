"""Las configuraciones elegidas por una corrida de tuning, corridas en Python y en C++ (`core.native_runner`)
sobre las mismas instancias de test y con varios presupuestos: cuánto más rápido es lo nativo y cuánto
gap gana con esa velocidad.

    python -m scripts.native_benchmark results/tune_run47 --catalog handwritten --budgets 1 5 \\
        --native examples.jobshop.native_parts --out bench.json

Gaps contra el mejor conocido de la corrida (el mejor de sus réplicas); con `--best-known` se le suma
lo que encuentre este script (si C++ mejora el mejor conocido, el gap de referencia baja).
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from random import Random
from statistics import mean

from scripts.tuning_replicas import load_replicas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--catalog", default="handwritten")
    ap.add_argument("--budgets", type=float, nargs="+", default=[1.0, 5.0])
    ap.add_argument("--native", required=True, help="módulo de piezas nativas (con `native` y `model(inst)`)")
    ap.add_argument("--problem", default="jobshop")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--skip-python", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    from core.native_runner import NativeRunner
    from llm.cycle import base_pack
    from tuning.cli import make_assembler

    reps = [json.loads((p / f"{args.catalog}.json").read_text()) for _, p in load_replicas(Path(args.run))]
    s = reps[0]["settings"]
    pack = base_pack(args.problem)
    test = pack.make_instances(s["test"], 500 + s["seed"] * 1000, pack.parse_size(str(s["size"])))
    bk = [min(x) for x in zip(*[r["test"]["best_known"] for r in reps])]
    assembler, _ = make_assembler(pack, args.catalog)
    nat = importlib.import_module(args.native)
    runner = NativeRunner(assembler, nat.native, nat.model)
    rows = []
    for k, r in enumerate(reps):
        cfg = r["test"]["tuned"]["config"]
        for b in args.budgets:
            for side, make in (("python", assembler.assemble), ("cpp", runner.assemble)):
                if side == "python" and args.skip_python:
                    continue
                run = make(cfg)
                for i, inst in enumerate(test):
                    for seed in range(args.seeds):
                        res = run(inst, Random(seed + i), b)
                        P = pack.problem_factory(inst)
                        ok = P.is_feasible(res.best_solution)
                        cost = P.objective(res.best_solution)
                        rows.append({"replica": k, "side": side, "budget": b, "instance": i, "seed": seed, "cost": cost,
                                     "feasible": ok, "iterations": res.iterations, "seconds": res.elapsed_time})
                sel = [x for x in rows if x["replica"] == k and x["side"] == side and x["budget"] == b]
                if sel:
                    print(f"r{k} {side:>6} {b:>5}s  gap {mean((x['cost'] - bk[x['instance']]) / bk[x['instance']] for x in sel):6.2%}"
                          f"  iter/s {sum(x['iterations'] for x in sel) / sum(x['seconds'] for x in sel):10,.0f}"
                          f"  {'' if all(x['feasible'] for x in sel) else 'INFACTIBLES'}  {r['test']['tuned']['summary']}", flush=True)
    best = [min([bk[i]] + [x["cost"] for x in rows if x["instance"] == i and x["feasible"]]) for i in range(len(test))]
    print("\nresumen (gap contra el mejor conocido de la corrida | contra el mejor incluyendo este script):")
    for side in ("python", "cpp"):
        for b in args.budgets:
            sel = [x for x in rows if x["side"] == side and x["budget"] == b]
            if not sel:
                continue
            g1 = mean((x["cost"] - bk[x["instance"]]) / bk[x["instance"]] for x in sel)
            g2 = mean((x["cost"] - best[x["instance"]]) / best[x["instance"]] for x in sel)
            ips = sum(x["iterations"] for x in sel) / sum(x["seconds"] for x in sel)
            print(f"  {side:>6} {b:>5}s  gap {g1:6.2%} | {g2:6.2%}   iteraciones/s {ips:12,.0f}")
    if args.out:
        Path(args.out).write_text(json.dumps({"run": args.run, "best_known": bk, "best": best, "rows": rows}))


if __name__ == "__main__":
    main()
