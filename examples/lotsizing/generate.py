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

from llm import OpenAIClient, TokenUsage, TranscriptClient, generate_slot

from .catalog import build_registry
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
    # Componentes que ya existen en el catálogo: el gate de diversidad los usa para que el
    # modelo no reinvente `setup_flip` con otro nombre (corrida 5: Jaccard 1,00).
    registry = build_registry()
    all_stats = {}
    for slot in args.slots:
        probe = contexts[0].diversity_probe
        peer_problem = probe.problem if probe is not None else contexts[0].problem
        peers = [
            (spec_c.name, spec_c.make(peer_problem, **spec_c.default_params()))
            for spec_c in registry.for_slot(slot)
        ]
        if peers:
            print(f"[{slot}] comparando diversidad contra {[n for n, _ in peers]}")
        accepted, stats = generate_slot(
            client, spec, slot, args.n, contexts, args.workspace,
            max_rounds=args.rounds, catalog_peers=peers,
            avoid_names=[n for n, _ in peers],
        )
        all_stats[slot] = {
            "requested": stats.requested, "parsed": stats.parsed, "accepted": stats.accepted,
            "llm_calls": stats.llm_calls, "llm_seconds": round(stats.llm_seconds, 1),
            "rejections_by_layer": dict(stats.rejections_by_layer),
            "rounds_per_accepted": stats.rounds_per_accepted, "abandoned": stats.abandoned,
            "accepted_files": [str(c.path) for c in accepted],
            "tokens": stats.tokens.as_dict(inner.model),
        }
    total = TokenUsage()
    for s in all_stats.values():
        t = s["tokens"]
        total.add(TokenUsage(t["input_tokens"], t["output_tokens"], t.get("cached_input_tokens", 0),
                             t.get("reasoning_tokens", 0), t["calls"]))
    all_stats["_run"] = {
        "model": inner.model, "provider": args.provider,
        "tokens": total.as_dict(inner.model),
        "note": ("costo estimado con LLM_PRICE_IN/LLM_PRICE_OUT (USD por millón de tokens)"
                 if total.cost_usd(inner.model) is not None
                 else "define LLM_PRICE_IN y LLM_PRICE_OUT (USD por millón de tokens) para estimar el costo"),
    }
    if total.total_tokens:
        print(f"\nTokens de la corrida: {total}")
    out = Path(args.workspace) / "stats.json"
    out.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False))
    print(f"Resumen guardado en {out}")


if __name__ == "__main__":
    main()
