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


def render(stats: dict) -> str:
    out = ["| slot | aceptados | rondas | rechazos por capa | abandonados | llamadas | s |", "|---|---|---|---|---|---|---|"]
    tot_acc = tot_par = tot_calls = 0
    tot_s = 0.0
    for slot, s in stats.items():
        rounds = ", ".join(f"`{k}`:{v}" for k, v in s.get("rounds_per_accepted", {}).items()) or "—"
        layers = ", ".join(f"{k} × {v}" for k, v in s.get("rejections_by_layer", {}).items()) or "ninguno"
        aband = ", ".join(f"`{n}`" for n in s.get("abandoned", [])) or "—"
        out.append(
            f"| `{slot}` | {s['accepted']}/{s['parsed']} | {rounds} | {layers} | {aband} "
            f"| {s['llm_calls']} | {s['llm_seconds']:.0f} |"
        )
        tot_acc += s["accepted"]; tot_par += s["parsed"]
        tot_calls += s["llm_calls"]; tot_s += s["llm_seconds"]
    out.append(f"| **total** | **{tot_acc}/{tot_par}** | | | | {tot_calls} | {tot_s:.0f} |")

    if tot_par and tot_acc == tot_par:
        out += ["", "> Todos los componentes fueron aceptados a la primera. Ojo: eso puede significar que el",
                "> validador no tiene dientes para estos slots, no solo que el modelo acertó. Compara con",
                "> `benchmark_components` (utilidad y diversidad) antes de concluir."]
    return "\n".join(out)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "generated/clsp/stats.json")
    if not path.exists():
        print(f"_No se encontró `{path}`._")
        return
    print(render(json.loads(path.read_text())))


if __name__ == "__main__":
    main()
