"""Reevalúa en test la configuración que eligió cada réplica de una corrida de tuning, con el
catálogo actual de un workspace del ciclo (p.ej. después de la etapa de optimización), sin volver
a afinar. Mismas instancias, semillas y presupuesto que la corrida original.

    python -m scripts.reevaluate_configs results/tune_run32 --problem cvrp --variant tour \\
        --workspace generated/cvrp_tour_cycle2

Reporta, por réplica, el gap original y el nuevo contra el mejor conocido guardado, y la
diferencia pareada por instancia con IC95.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from scripts.tuning_replicas import _ci95, _gaps, load_replicas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--problem", required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--catalog", default="generated")
    ap.add_argument("--out", default=None, help="JSON con los resultados (opcional)")
    args = ap.parse_args()

    from tuning.cli import make_assembler
    from tuning.evaluation import score_config

    from llm.cycle import load_variant

    pack = load_variant(args.problem, args.variant, args.workspace, reference=False)
    reps = [(name, json.loads((p / f"{args.catalog}.json").read_text())) for name, p in load_replicas(Path(args.run))]
    s = reps[0][1]["settings"]
    test = pack.make_instances(s["test"], 500 + s["seed"] * 1000, pack.parse_size(str(s["size"])))
    assembler, _ = make_assembler(pack, args.catalog, args.workspace, skeletons=s["skeletons"] if s["skeletons"] != "all" else None)
    seeds = tuple(range(s.get("seeds_test", 3)))
    rows, diffs_all = [], []
    for name, payload in reps:
        t = payload["test"]
        bk = t["best_known"]
        score = score_config(assembler, "reevaluado", t["tuned"]["config"], test, s["budget"], seeds)
        g_old, g_new = _gaps(t["tuned"]["per_instance"], bk), _gaps(score.per_instance, bk)
        rows.append({"replica": name, "summary": t["tuned"]["summary"], "gap_before": mean(g_old), "gap_after": mean(g_new)})
        diffs_all.append([o - n for o, n in zip(g_old, g_new)])  # > 0: mejora
        print(f"{name}: {mean(g_old):.2%} → {mean(g_new):.2%}  {t['tuned']['summary']}")
    per_inst = [mean(d[k] for d in diffs_all) for k in range(len(test))]
    lo, hi = _ci95(per_inst)
    print(f"mejora media {mean(per_inst):+.2%} de gap (positiva: el catálogo actual es mejor), IC95 [{lo:+.2%}, {hi:+.2%}]")
    if args.out:
        Path(args.out).write_text(json.dumps({"rows": rows, "mean_gain": mean(per_inst), "ci95": [lo, hi]}, indent=2))


if __name__ == "__main__":
    main()
