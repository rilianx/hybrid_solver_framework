"""Compara corridas de tuning con réplicas de dos variantes de un mismo problema (p.ej. `cvrp`,
rutas, contra `cvrp_tour`, gran tour + Split).

    python -m scripts.compare_packs results/tune_runA results/tune_runB [--catalog generated]

Cada representación es un problema distinto para el framework, pero las variantes comparten
instancias y casos de prueba: sus modelos pasan los mismos casos, así que sus costos significan
lo mismo y se comparan instancia por instancia. Exige que las dos corridas usen las mismas
instancias de test (mismo tamaño, semilla y cantidad); usa un mejor conocido común a todas las
réplicas de ambas y reporta, por variante, el gap del afinado entre réplicas y la diferencia
pareada por instancia (promediada sobre réplicas) con IC95 por bootstrap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev

from scripts.tuning_replicas import _ci95, _gaps, load_replicas


def _load(root: Path, catalog: str) -> list[dict]:
    reps = [json.loads((p / f"{catalog}.json").read_text()) for _, p in load_replicas(root) if (p / f"{catalog}.json").exists()]
    if not reps:
        raise SystemExit(f"no hay réplicas con {catalog}.json en {root}")
    return reps


def _instances_key(payload: dict) -> tuple:
    s = payload["settings"]
    return (s.get("size"), s.get("seed"), s["test"], s["budget"])


def compare(a_root: Path, b_root: Path, catalog: str = "generated") -> tuple[str, dict]:
    a, b = _load(a_root, catalog), _load(b_root, catalog)
    if _instances_key(a[0]) != _instances_key(b[0]):
        raise SystemExit(f"las corridas no usan las mismas instancias de test: {_instances_key(a[0])} vs {_instances_key(b[0])}")
    n = len(a[0]["test"]["tuned"]["per_instance"])
    runs = a + b
    best = [min(min(r["test"]["best_known"][k] for r in runs),
                min(r["test"]["tuned"]["per_instance"][k] for r in runs)) for k in range(n)]
    ga = [_gaps(r["test"]["tuned"]["per_instance"], best) for r in a]
    gb = [_gaps(r["test"]["tuned"]["per_instance"], best) for r in b]
    per_a = [mean(g[k] for g in ga) for k in range(n)]
    per_b = [mean(g[k] for g in gb) for k in range(n)]
    diffs = [y - x for x, y in zip(per_a, per_b)]  # > 0: A es mejor
    lo, hi = _ci95(diffs)
    ma, mb = [mean(g) for g in ga], [mean(g) for g in gb]
    data = {"a": str(a_root), "b": str(b_root), "best_known": best,
            "a_gaps": ma, "b_gaps": mb, "mean_diff": mean(diffs), "ci95": [lo, hi], "significant": lo > 0 or hi < 0,
            "a_choices": [r["tuning"]["best_summary"] for r in a], "b_choices": [r["tuning"]["best_summary"] for r in b]}
    sd = lambda xs: pstdev(xs) if len(xs) > 1 else 0.0  # noqa: E731
    md = [f"## `{a_root.name}` contra `{b_root.name}` (catálogo `{catalog}`, {n} instancias de test)", "",
          "| variante | réplicas | gap afinado (media) | desvío | por réplica |", "|---|---|---|---|---|",
          f"| A `{a_root.name}` | {len(ma)} | {mean(ma):.2%} | {sd(ma):.2%} | " + " / ".join(f"{g:.2%}" for g in ma) + " |",
          f"| B `{b_root.name}` | {len(mb)} | {mean(mb):.2%} | {sd(mb):.2%} | " + " / ".join(f"{g:.2%}" for g in mb) + " |",
          "", f"Diferencia B − A por instancia: {mean(diffs):+.2%} de gap (positiva: A es mejor), IC95 [{lo:+.2%}, {hi:+.2%}]"
          + ("." if data["significant"] else " — **no se distingue del ruido**."),
          "", "Elegido por réplica:", ""]
    md += [f"- A: `{s}`" for s in data["a_choices"]] + [f"- B: `{s}`" for s in data["b_choices"]]
    return "\n".join(md), data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--catalog", default="generated")
    args = ap.parse_args()
    md, _ = compare(Path(args.a), Path(args.b), args.catalog)
    print(md)


if __name__ == "__main__":
    main()
