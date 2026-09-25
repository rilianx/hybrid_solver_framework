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
    gap = lambda row: f"{row['mean_gap']:.2%}" if "mean_gap" in row else "—"  # noqa: E731
    out = [f"### Catálogo `{payload['catalog']}`",
           "",
           f"{s['trials']} trials · {s['budget']} s/corrida · {s['train']} train / {s['test']} test ({s.get('problem', 'clsp')} {s['size'] if 'size' in s else str(s['items']) + '×' + str(s['periods'])}) · "
           f"{tun['n_failed']} configuraciones fallidas · {tun['seconds']:.0f} s de tuning",
           ""]
    extras = []
    if s.get("skeletons") and s["skeletons"] != "all":
        extras.append("esqueletos: " + ", ".join(f"`{k}`" for k in s["skeletons"]))
    if s.get("objective"):
        extras.append(f"objetivo de tuning: `{s['objective']}`")
    if s.get("ref_time"):
        extras.append(f"referencia del gap: mejor corrida o MIP completo {s['ref_time']:.0f} s")
    if extras:
        out += [" · ".join(extras), ""]
    if payload.get("generated_components"):
        out += ["Componentes LLM en el catálogo: " + ", ".join(f"`{n}`" for n in payload["generated_components"]), ""]
    num = (lambda v: f"{v:.4f}") if s.get("objective") == "ratio" else (lambda v: f"{v:.1f}")  # ratio: costo/lot-for-lot
    out += [f"**Mejor en train**: `{tun['best_summary']}` = {num(tun['best_cost'])}"
            + (f" (mejor default: {num(tun['best_default_cost'])}, `{tun['best_default_summary']}`)" if tun.get("best_default_cost") else ""),
            "",
            "| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |", "|---|---|---|---|---|---|"]
    t = test["tuned"]
    out.append(f"| **afinado** | **{gap(t)}** | **{t['mean']:.1f}** | {t['std']:.0f} | {pct(t['mean'])} | `{t['summary']}` |")
    for b in test["baselines"]:
        out.append(f"| {b['label']} | {gap(b)} | {b['mean']:.1f} | {b['std']:.0f} | {pct(b['mean'])} | `{b['summary']}` |")
    out += ["", f"Ganancia del afinado sobre el mejor default: **{test['gain_vs_best_baseline']:+.2%}**; "
            f"gana en {test['wins_per_instance']} instancias de test. Esqueletos explorados: "
            + ", ".join(f"{k} × {v}" for k, v in tun["skeleton_usage"].items()) + "."]
    pc = test.get("tuned_vs_best_baseline")
    if pc:
        out += ["", f"Afinado vs `{pc['b']}` (mejor default por gap): {pc['mean_diff']:+.2%} de gap a favor del afinado, "
                f"IC95 [{pc['ci95'][0]:+.2%}, {pc['ci95'][1]:+.2%}]"
                + ("." if pc["significant"] else " — **no se distingue del ruido** con estas instancias.")]
    if tun.get("reevaluated"):
        out += ["", "Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "
                "\"numéricos por defecto\" = los componentes de ese trial sin afinar sus parámetros):", "",
                "| trial | media | costos | configuración |", "|---|---|---|---|"]
        for r in sorted(tun["reevaluated"], key=lambda r: r["mean"]):
            chosen = r["number"] == tun.get("best_trial_number") and bool(r.get("twin")) == bool(tun.get("best_is_twin"))
            mark = " ✔" if chosen else ""
            tag = " (numéricos por defecto)" if r.get("twin") else "*" if r["enqueued"] else ""
            out.append(f"| {r['number']}{tag}{mark} | {r['mean']:.4f} | "
                       + ", ".join(f"{c:.4f}" for c in r["costs"]) + f" | `{r['summary']}` |")
    return "\n".join(out)


def render(out_dir: Path) -> str:
    parts = []
    for name in ("handwritten", "generated", "all"):
        p = out_dir / f"{name}.json"
        if p.exists():
            parts.append(render_catalog(json.loads(p.read_text())))
    cmp = out_dir / "comparison.json"
    if cmp.exists():
        c = json.loads(cmp.read_text())
        if "relative_gain_from_llm_catalog" in c:
            d = c["relative_gain_from_llm_catalog"]
            verdict = "el catálogo ampliado **ayuda**" if d > 0.005 else ("el catálogo ampliado **diluye**" if d < -0.005 else "**empate**: el tuner eligió lo mismo o equivalente")
            gaps = (f" Gap medio vs mejor conocido: a mano {c['handwritten_tuned_gap']:.2%}, con LLM {c['all_tuned_gap']:.2%}."
                    if "handwritten_tuned_gap" in c else "")
            parts.append("### ¿Ayuda o diluye?\n\n"
                         f"Afinado en test — a mano: {c['handwritten_tuned_test']:.1f} (`{c['handwritten_best']}`) · "
                         f"con LLM: {c['all_tuned_test']:.1f} (`{c['all_best']}`) → **{d:+.2%}**, {verdict}.{gaps}")
        if "relative_gain_generated_only" in c:
            d = c["relative_gain_generated_only"]
            verdict = ("solo generados **supera** a lo de mano" if d > 0.005 else
                       ("solo generados **queda por debajo** de lo de mano" if d < -0.005 else "**empate** entre solo generados y a mano"))
            parts.append("### Solo generados vs a mano\n\n"
                         f"Afinado en test — a mano: {c['handwritten_tuned_test']:.1f}, gap {c['handwritten_tuned_gap']:.2%} "
                         f"(`{c['handwritten_best']}`) · solo LLM: {c['generated_tuned_test']:.1f}, gap {c['generated_tuned_gap']:.2%} "
                         f"(`{c['generated_best']}`) → **{d:+.2%}**, {verdict}.")
    if not parts:
        return f"> No hay resultados en `{out_dir}`: el tuning no llegó a completarse (revisa el log)."
    return "\n\n".join(parts)


def main() -> None:
    print(render(Path(sys.argv[1] if len(sys.argv) > 1 else "tuning_out")))


if __name__ == "__main__":
    main()
