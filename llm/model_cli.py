"""Genera el `ProblemModel` completo de un problema con un LLM (§6.1). Genérico: recibe un
`ProblemPack` con `make_model_spec` (`python -m examples.cvrp.generate_model`).

Guarda cada ronda en `<workspace>/problem_model/model_r<k>.py`, las transcripciones y un
`stats.json` con las rondas, los rechazos y, si se aceptó, el chequeo cruzado contra el
modelo de referencia del pack (óptimo del MIP en las mismas micro-instancias).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.problem_pack import ProblemPack

from .client import OpenAIClient, TranscriptClient
from .model_generator import cross_check, generate_problem_model, validate_model_module


def main(pack: ProblemPack, argv: list[str] | None = None) -> None:
    if pack.make_model_spec is None:
        raise SystemExit(f"el pack {pack.name} no define make_model_spec")
    ap = argparse.ArgumentParser(prog=f"python -m {pack.module}.generate_model")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--model", default=None)
    ap.add_argument("--workspace", default=f"generated/{pack.name}_model")
    ap.add_argument("--instances", type=int, default=3, help="micro-instancias de validación")
    args = ap.parse_args(argv)

    if args.provider == "openai":
        inner = OpenAIClient(model=args.model or "gpt-5.4-mini")
    else:
        from .client import AnthropicClient

        inner = AnthropicClient(model=args.model or "claude-sonnet-4-5")
    client = TranscriptClient(inner, Path(args.workspace) / "transcript")
    spec = pack.make_model_spec()
    micro = pack.make_instances(args.instances, 900, pack.parse_size(pack.micro_size or pack.default_size))
    res = generate_problem_model(client, spec, micro, args.workspace, max_rounds=args.rounds)
    stats = {"problem": pack.name, "model": inner.model, "accepted": res.path is not None, "rounds": res.rounds,
             "llm_calls": res.llm_calls, "seconds": round(res.seconds, 1), "tokens": res.tokens.as_dict(inner.model),
             "rejections": res.reports, "accepted_file": str(res.path) if res.path else None}
    if res.path is not None:
        _, module = validate_model_module(res.path, micro, forbidden_modules=spec.forbidden_modules)
        check = cross_check(module, pack.problem_factory, pack.make_instances(3, 950, pack.parse_size(pack.micro_size)))
        stats["cross_check"] = check
        print("chequeo cruzado (óptimo MIP generado vs referencia):",
              ", ".join(f"{r['generated']} vs {r['reference']} {'✔' if r['match'] else '✘'}" for r in check))
    out = Path(args.workspace) / "stats.json"
    out.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"Resumen guardado en {out}")
