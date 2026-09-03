"""Convierte `stats.json` (salida de examples/*/generate.py) en una tabla Markdown.

Se usa en CI para escribir el resumen de la corrida en `$GITHUB_STEP_SUMMARY`,
de modo que las tasas de aprobación por capa y las rondas de corrección (§9.3)
se lean en el navegador sin descargar artefactos.

    python -m scripts.stats_summary generated/clsp/stats.json >> "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _tokens(s: dict) -> dict:
    return s.get("tokens") or {}


def render(stats: dict) -> str:
    run = stats.pop("_run", {})
    out = ["| slot | aceptados | rondas | rechazos por capa | abandonados | llamadas | s | tokens (in+out) |",
           "|---|---|---|---|---|---|---|---|"]
    tot_acc = tot_par = tot_calls = tot_rej = 0
    tot_s = 0.0
    for slot, s in stats.items():
        rounds = ", ".join(f"`{k}`:{v}" for k, v in s.get("rounds_per_accepted", {}).items()) or "—"
        layers = ", ".join(f"{k} × {v}" for k, v in s.get("rejections_by_layer", {}).items()) or "ninguno"
        aband = ", ".join(f"`{n}`" for n in s.get("abandoned", [])) or "—"
        t = _tokens(s)
        toks = f"{t['total_tokens']:,} ({t['input_tokens']:,}+{t['output_tokens']:,})" if t.get("total_tokens") else "—"
        out.append(
            f"| `{slot}` | {s['accepted']}/{s['parsed']} | {rounds} | {layers} | {aband} "
            f"| {s['llm_calls']} | {s['llm_seconds']:.0f} | {toks} |"
        )
        tot_acc += s["accepted"]; tot_par += s["parsed"]
        tot_calls += s["llm_calls"]; tot_s += s["llm_seconds"]
        tot_rej += sum(s.get("rejections_by_layer", {}).values())
    rt = _tokens(run)
    tot_toks = f"**{rt['total_tokens']:,}** ({rt['input_tokens']:,}+{rt['output_tokens']:,})" if rt.get("total_tokens") else "—"
    out.append(f"| **total** | **{tot_acc}/{tot_par}** | | | | {tot_calls} | {tot_s:.0f} | {tot_toks} |")
    if rt.get("total_tokens"):
        line = f"Modelo `{run.get('model', '?')}` · {rt['total_tokens']:,} tokens en {rt['calls']} llamadas"
        if rt.get("cached_input_tokens"):
            line += f" · {rt['cached_input_tokens']:,} de entrada servidos desde caché"
        if rt.get("reasoning_tokens"):
            line += f" · {rt['reasoning_tokens']:,} de razonamiento"
        if rt.get("cost_usd") is not None:
            line += f" · **≈ USD {rt['cost_usd']:.4f}**"
        else:
            line += " · costo: define `LLM_PRICE_IN` y `LLM_PRICE_OUT` (USD por millón de tokens) para estimarlo"
        out += ["", line]

    if tot_par and tot_acc == tot_par and tot_rej == 0:
        out += ["", "> Todos los componentes fueron aceptados a la primera, sin un solo rechazo en ninguna capa.",
                "> Ojo: eso puede significar que el",
                "> validador no tiene dientes para estos slots, no solo que el modelo acertó. Compara con",
                "> `benchmark_components` (utilidad y diversidad) antes de concluir."]
    elif tot_par and tot_acc == tot_par:
        out += ["", f"> Todos los componentes terminaron aceptados, pero tras {tot_rej} rechazo(s) y su(s) "
                "corrección(es): el ciclo generar→validar→corregir hizo trabajo. Aun así, la validez no es "
                "utilidad: contrasta con `benchmark_components`."]
    return "\n".join(out)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "generated/clsp/stats.json")
    if not path.exists():
        print(f"> **La generación no dejó `{path}`**, así que no llegó a completarse.")
        print(">")
        print("> Revisa cuál paso quedó en rojo más arriba:")
        print("> - *Comprobar que la clave está configurada* → falta el secreto `OPENAI_API_KEY`")
        print(">   (Settings → Secrets and variables → Actions; el nombre debe coincidir exacto).")
        print("> - *Instalar dependencias* → problema de `pip install -r requirements.txt`.")
        print("> - *Generar y validar* → error real de la API o del código; el log de abajo lo dice.")
        return
    print(render(json.loads(path.read_text())))


if __name__ == "__main__":
    main()
