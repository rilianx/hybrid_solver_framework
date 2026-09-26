"""Agrega réplicas de una corrida de tuning (mismas instancias, distinta semilla del tuner).

    python -m scripts.tuning_replicas results/tune_runN      # r0/, r1/, ... con <catálogo>.json

Runs 15-22: con 5 instancias de train y 40 trials, dos semillas del tuner difieren en 3 a 4.5
puntos de gap en test, más que casi todas las diferencias entre catálogos que se comparaban
con una sola corrida. Este resumen trata la corrida de tuning como variable aleatoria:

- Un solo "mejor conocido" por instancia para todas las réplicas (el mínimo entre ellas: la
  referencia del MIP con límite de tiempo también varía), y los gaps se recalculan con él.
- Por réplica: gap del afinado en test y qué eligió.
- Entre réplicas: media, desvío, mínimo y máximo del gap del afinado.
- Afinado vs la mejor configuración no afinada (defaults y defaults con un componente
  cambiado, que son las mismas en todas las réplicas; se promedia su gap entre réplicas):
  diferencia por instancia promediada sobre réplicas, con IC95 por bootstrap sobre las
  instancias, y en cuántas réplicas el afinado queda por delante.

Escribe el Markdown en stdout y `replicas.json` en el directorio.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from random import Random
from statistics import mean, pstdev
from typing import Any

CATALOGS = ("handwritten", "generated", "all")


def _gaps(per_instance: list[float], best: list[float]) -> list[float]:
    return [(c - b) / abs(b) if b else 0.0 for c, b in zip(per_instance, best)]


def _ci95(diffs: list[float], n_boot: int = 4000, seed: int = 0) -> tuple[float, float]:
    rng = Random(seed)
    boots = sorted(mean(rng.choice(diffs) for _ in diffs) for _ in range(n_boot))
    return boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]


def load_replicas(root: Path) -> list[tuple[str, Path]]:
    reps = sorted((p for p in root.iterdir() if p.is_dir() and p.name.startswith("r") and p.name[1:].isdigit()),
                  key=lambda p: int(p.name[1:]))
    return [(p.name, p) for p in reps]


def aggregate_catalog(payloads: list[tuple[str, dict]]) -> dict[str, Any]:
    tests = [(name, p["test"]) for name, p in payloads]
    n = len(tests[0][1]["tuned"]["per_instance"])
    best = [min(min(t["best_known"][k] for _, t in tests),
                min(min(s["per_instance"][k] for s in [t["tuned"], *t["baselines"]]) for _, t in tests))
            for k in range(n)]
    reps = []
    for (name, t), (_, p) in zip(tests, payloads):
        reps.append({"replica": name, "seed": p["settings"].get("tuner_seed"),
                     "summary": t["tuned"]["summary"], "gaps": _gaps(t["tuned"]["per_instance"], best)})
        reps[-1]["mean_gap"] = mean(reps[-1]["gaps"])
    # las configuraciones no afinadas son las mismas en todas las réplicas: gap medio por etiqueta
    labels = set.intersection(*({b["label"] for b in t["baselines"]} for _, t in tests))
    base = {}
    for lab in labels:
        per = [_gaps(next(b for b in t["baselines"] if b["label"] == lab)["per_instance"], best) for _, t in tests]
        base[lab] = [mean(g[k] for g in per) for k in range(n)]
    best_label = min(base, key=lambda lab: mean(base[lab]))
    diffs = [mean(base[best_label][k] - r["gaps"][k] for r in reps) for k in range(n)]  # > 0: el afinado es mejor
    lo, hi = _ci95(diffs)
    tuned = [r["mean_gap"] for r in reps]
    return {
        "best_known": best,
        "replicas": reps,
        "tuned_mean_gap": mean(tuned), "tuned_sd_gap": pstdev(tuned) if len(tuned) > 1 else 0.0,
        "tuned_min_gap": min(tuned), "tuned_max_gap": max(tuned),
        "best_untuned": best_label, "best_untuned_gap": mean(base[best_label]),
        "default_gaps": {lab: mean(g) for lab, g in sorted(base.items(), key=lambda kv: mean(kv[1]))},
        "tuned_vs_best_untuned": {"mean_diff": mean(diffs), "ci95": [lo, hi], "significant": lo > 0 or hi < 0,
                                  "replicas_ahead": sum(1 for r in reps if r["mean_gap"] < mean(base[best_label]))},
    }


def render(root: Path) -> tuple[str, dict[str, Any]]:
    reps = load_replicas(root)
    if not reps:
        return f"> No hay réplicas (`r0/`, `r1/`, …) en `{root}`.", {}
    out, data = [f"## Réplicas del tuning ({len(reps)})", ""], {}
    for cat in CATALOGS:
        payloads = [(name, json.loads((p / f"{cat}.json").read_text())) for name, p in reps if (p / f"{cat}.json").exists()]
        if not payloads:
            continue
        a = aggregate_catalog(payloads)
        data[cat] = a
        s = payloads[0][1]["settings"]
        pc = a["tuned_vs_best_untuned"]
        out += [f"### Catálogo `{cat}`", "",
                f"{s['trials']} trials · {s['budget']} s · {s['train']} train / {s['test']} test · "
                f"gaps contra el mejor conocido común a las réplicas", "",
                "| réplica | semilla del tuner | gap afinado | configuración elegida |", "|---|---|---|---|"]
        out += [f"| {r['replica']} | {r['seed'] if r['seed'] is not None else '—'} | {r['mean_gap']:.2%} | `{r['summary']}` |"
                for r in a["replicas"]]
        out += ["",
                f"**Afinado entre réplicas**: media {a['tuned_mean_gap']:.2%}, desvío {a['tuned_sd_gap']:.2%}, "
                f"rango [{a['tuned_min_gap']:.2%}, {a['tuned_max_gap']:.2%}].", "",
                f"**Mejor no afinado** (media entre réplicas): `{a['best_untuned']}` = {a['best_untuned_gap']:.2%}. "
                f"Afinado vs ese: {pc['mean_diff']:+.2%} de gap a favor del afinado, IC95 [{pc['ci95'][0]:+.2%}, "
                f"{pc['ci95'][1]:+.2%}] sobre las instancias"
                + ("" if pc["significant"] else " (**no se distingue del ruido**)")
                + f"; el afinado queda por delante en {pc['replicas_ahead']} de {len(a['replicas'])} réplicas.", ""]
    return "\n".join(out), data


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    md, data = render(root)
    if data:
        (root / "replicas.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(md)


if __name__ == "__main__":
    main()
