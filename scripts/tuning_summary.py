"""Convierte `tuning_out/*.json` (salida de examples.lotsizing.tune) en Markdown para
el resumen de la corrida en GitHub Actions.

    python -m scripts.tuning_summary tuning_out >> "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def render_catalog(payload: dict) -> str:
    s, tun, test = payload["settings"], payload["tuning"], payload["test"]
    ref = test.get("reference")
    pct = (lambda v: f"{(ref - v) / ref:+.1%}") if ref else (lambda v: "")
    out = [f"### Catálogo `{payload['catalog']}`",
           "",
           f"{s['trials']} trials · {s['budget']} s/corrida · {s['train']} train / {s['test']} test ({s['items']}×{s['periods']}) · "
           f"{tun['n_failed']} configuraciones fallidas · {tun['seconds']:.0f} s de tuning",
           ""]
    if payload.get("generated_components"):
        out += ["Componentes LLM en el catálogo: " + ", ".join(f"`{n}`" for n in payload["generated_components"]), ""]
    out += [f"**Mejor en train**: `{tun['best_summary']}` = {tun['best_cost']:.1f}"
            + (f" (mejor default: {tun['best_default_cost']:.1f}, `{tun['best_default_summary']}`)" if tun.get("best_default_cost") else ""),
            "",
            "| en TEST | costo medio | ± | vs lot-for-lot | configuración |", "|---|---|---|---|---|"]
    t = test["tuned"]
    out.append(f"| **afinado** | **{t['mean']:.1f}** | {t['std']:.0f} | {pct(t['mean'])} | `{t['summary']}` |")
    for b in test["baselines"]:
        out.append(f"| {b['label']} | {b['mean']:.1f} | {b['std']:.0f} | {pct(b['mean'])} | `{b['summary']}` |")
    out += ["", f"Ganancia del afinado sobre el mejor default: **{test['gain_vs_best_baseline']:+.2%}**; "
            f"gana en {test['wins_per_instance']} instancias de test. Esqueletos explorados: "
            + ", ".join(f"{k} × {v}" for k, v in tun["skeleton_usage"].items()) + "."]
    return "\n".join(out)


def render(out_dir: Path) -> str:
    parts = []
    for name in ("handwritten", "all"):
        p = out_dir / f"{name}.json"
        if p.exists():
            parts.append(render_catalog(json.loads(p.read_text())))
    cmp = out_dir / "comparison.json"
    if cmp.exists():
        c = json.loads(cmp.read_text())
        d = c["relative_gain_from_llm_catalog"]
        verdict = "el catálogo ampliado **ayuda**" if d > 0.005 else ("el catálogo ampliado **diluye**" if d < -0.005 else "**empate**: el tuner eligió lo mismo o equivalente")
        parts.append("### ¿Ayuda o diluye?\n\n"
                     f"Afinado en test — a mano: {c['handwritten_tuned_test']:.1f} (`{c['handwritten_best']}`) · "
                     f"con LLM: {c['all_tuned_test']:.1f} (`{c['all_best']}`) → **{d:+.2%}**, {verdict}.")
    if not parts:
        return f"> No hay resultados en `{out_dir}`: el tuning no llegó a completarse (revisa el log)."
    return "\n\n".join(parts)


def main() -> None:
    print(render(Path(sys.argv[1] if len(sys.argv) > 1 else "tuning_out")))


if __name__ == "__main__":
    main()
