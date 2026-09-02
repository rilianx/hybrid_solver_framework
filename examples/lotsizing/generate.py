"""Genera componentes para el CLSP con un LLM real y los valida (§6, §9.3).

    export OPENAI_API_KEY=...            # o ANTHROPIC_API_KEY con --provider anthropic
    python -m examples.lotsizing.generate --slots neighborhood destruction --n 3

Guarda los módulos (aceptados y rechazados, por ronda) en `generated/clsp/<slot>/`,
la transcripción de cada llamada en `generated/clsp/transcript/`, y un resumen
`stats.json` con tasas de aprobación por capa y rondas de corrección.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm import OpenAIClient, TranscriptClient, generate_slot

from .llm_spec import make_contexts, make_spec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", nargs="+", default=["neighborhood", "destruction"])
    ap.add_argument("--n", type=int, default=3, help="variantes por slot")
    ap.add_argument("--rounds", type=int, default=3, help="rondas máximas (1 generación + correcciones)")
    ap.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--model", default=None)
    ap.add_argument("--workspace", default="generated/clsp")
    args = ap.parse_args()

    if args.provider == "openai":
        inner = OpenAIClient(model=args.model or "gpt-5.4-mini")
    else:
        from llm import AnthropicClient

        inner = AnthropicClient(model=args.model or "claude-sonnet-4-5")
    client = TranscriptClient(inner, Path(args.workspace) / "transcript")

    spec, contexts = make_spec(), make_contexts()
    all_stats = {}
    for slot in args.slots:
        accepted, stats = generate_slot(client, spec, slot, args.n, contexts, args.workspace, max_rounds=args.rounds)
        all_stats[slot] = {
            "requested": stats.requested, "parsed": stats.parsed, "accepted": stats.accepted,
            "llm_calls": stats.llm_calls, "llm_seconds": round(stats.llm_seconds, 1),
            "rejections_by_layer": dict(stats.rejections_by_layer),
            "rounds_per_accepted": stats.rounds_per_accepted, "abandoned": stats.abandoned,
            "accepted_files": [str(c.path) for c in accepted],
        }
    out = Path(args.workspace) / "stats.json"
    out.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False))
    print(f"\nResumen guardado en {out}")


if __name__ == "__main__":
    main()
