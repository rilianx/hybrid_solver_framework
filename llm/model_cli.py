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
    ap.add_argument("--instances", type=int, default=3, help="micro-instancias de validación (modo monolítico)")
    ap.add_argument("--monolithic", action="store_true",
                    help="el modelo en un solo módulo (corrida 19), en vez de por piezas validadas con casos de prueba")
    args = ap.parse_args(argv)

    if args.provider == "openai":
        inner = OpenAIClient(model=args.model or "gpt-5.4-mini")
    else:
        from .client import AnthropicClient

        inner = AnthropicClient(model=args.model or "claude-sonnet-4-5")
    client = TranscriptClient(inner, Path(args.workspace) / "transcript")
    spec = pack.make_model_spec()
    if not args.monolithic and pack.load_cases is not None:
        _parts(pack, spec, client, inner, args)
        return
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


def _parts(pack: ProblemPack, spec, client, inner, args) -> None:
    from core.model_parts import PartsModel

    from .parts_generator import generate_problem_model_parts

    cases = pack.load_cases()
    res = generate_problem_model_parts(client, spec, cases, args.workspace, max_rounds=args.rounds)
    stats = {"problem": pack.name, "mode": "parts", "model": inner.model, "accepted": res.path is not None,
             "cases": {"visible": sum(c.visible for c in cases), "hidden": sum(not c.visible for c in cases)},
             "heuristic": {"accepted": res.heuristic.accepted, "rounds": res.heuristic.rounds, "rejections": res.heuristic.reports},
             "mip": {"accepted": res.mip.accepted, "rounds": res.mip.rounds, "rejections": res.mip.reports},
             "llm_calls": res.llm_calls, "seconds": round(res.seconds, 1), "tokens": res.tokens.as_dict(inner.model),
             "accepted_file": str(res.path) if res.path else None}
    if res.path is not None:
        from core.validation.syntactic import load_module

        module, _ = load_module(res.path)
        micro = pack.make_instances(3, 950, pack.parse_size(pack.micro_size))
        stats["cross_check"] = cross_check(types_namespace(module), pack.problem_factory, micro)
    out = Path(args.workspace) / "stats.json"
    out.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"Resumen guardado en {out}")


def types_namespace(parts_module):
    """Adapta un módulo de piezas a lo que espera `cross_check` (build_problem_model)."""
    from types import SimpleNamespace

    from core.model_parts import PartsModel

    return SimpleNamespace(build_problem_model=lambda inst: PartsModel(parts_module, inst))
