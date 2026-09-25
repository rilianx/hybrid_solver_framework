"""Genera componentes para un problema con un LLM real y los valida (§6, §9.3). Genérico:
recibe un `ProblemPack` (`python -m examples.lotsizing.generate …`, `python -m examples.cvrp.generate …`).

    export OPENAI_API_KEY=...            # o ANTHROPIC_API_KEY con --provider anthropic
    python -m examples.cvrp.generate --slots neighborhood destruction --n 3

Guarda los módulos (aceptados y rechazados, por ronda) en `generated/<problema>/<slot>/`,
la transcripción de cada llamada en `…/transcript/`, y un resumen `stats.json` con tasas
de aprobación por capa y rondas de corrección.

Con `--from-scratch` el modelo no ve los componentes escritos a mano: la diversidad se
exige solo entre los aceptados de la misma corrida, el prompt no nombra los existentes y
el feedback no muestra los movimientos del vecindario de referencia.

Con `--planner` cada slot se genera con `llm.planner`: un planificador propone ideas en
texto, cada idea se implementa y corrige en paralelo (`--workers` por slot) y el gate de
diversidad se aplica al unir; si faltan componentes, se replanifica (`--replans`). Los
slots también corren en paralelo entre sí.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core.problem_pack import ProblemPack

from .catalog import build_registry
from .client import OpenAIClient, TokenUsage, TranscriptClient
from .generator import generate_slot
from .planner import generate_slot_planned


def main(pack: ProblemPack, argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog=f"python -m {pack.module}.generate")
    ap.add_argument("--slots", nargs="+", default=["neighborhood", "destruction"])
    ap.add_argument("--n", type=int, default=3, help="variantes por slot")
    ap.add_argument("--rounds", type=int, default=3, help="rondas máximas (1 generación + correcciones)")
    ap.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--model", default=None)
    ap.add_argument("--workspace", default=pack.default_workspace)
    ap.add_argument("--from-scratch", action="store_true",
                    help="sin componentes de referencia: ni diversidad contra el catálogo, ni nombres, ni vecindario de referencia")
    ap.add_argument("--catalog-diversity", choices=["annotate", "reject"], default="annotate",
                    help="annotate (default): la diversidad se exige solo dentro de la corrida y el parecido con el "
                         "catálogo se anota en stats.json; reject: se rechaza lo parecido a un componente del catálogo")
    ap.add_argument("--planner", action="store_true", help="planificador de ideas + implementación en paralelo")
    ap.add_argument("--ideas", type=int, default=None, help="ideas por slot en la primera planificación (default: --n)")
    ap.add_argument("--workers", type=int, default=3, help="implementaciones en paralelo por slot (con --planner)")
    ap.add_argument("--replans", type=int, default=1, help="replaneos máximos si faltan componentes (con --planner)")
    args = ap.parse_args(argv)

    if args.provider == "openai":
        inner = OpenAIClient(model=args.model or "gpt-5.4-mini")
    else:
        from .client import AnthropicClient

        inner = AnthropicClient(model=args.model or "claude-sonnet-4-5")
    client = TranscriptClient(inner, Path(args.workspace) / "transcript")

    spec, contexts = pack.make_spec(), pack.make_contexts(reference_free=args.from_scratch, combination=True)
    # Componentes que ya existen en el catálogo: el gate de diversidad los usa para que el
    # modelo no reinvente el operador elemental con otro nombre (CLSP, corrida 5: Jaccard 1,00). Desde cero
    # no hay pares: la diversidad se mide solo entre los aceptados de esta corrida.
    registry = build_registry(pack)
    all_stats = {}
    t_run = time.perf_counter()

    def run_slot(slot):
        probe = contexts[0].diversity_probe
        peer_problem = probe.problem if probe is not None else contexts[0].problem
        peers = [] if args.from_scratch else [
            (spec_c.name, spec_c.make(peer_problem, **spec_c.default_params()))
            for spec_c in registry.for_slot(slot)
        ]
        if peers:
            print(f"[{slot}] comparando diversidad contra {[n for n, _ in peers]}")
        reject = args.catalog_diversity == "reject"
        policy = dict(catalog_peers=peers if reject else None, annotate_peers=None if reject else peers,
                      avoid_names=[n for n, _ in peers], avoid_ideas=reject)
        if args.planner:
            return generate_slot_planned(
                client, spec, slot, args.n, contexts, args.workspace, max_rounds=args.rounds,
                n_ideas=args.ideas, max_workers=args.workers, max_replans=args.replans, **policy,
            )
        return generate_slot(client, spec, slot, args.n, contexts, args.workspace, max_rounds=args.rounds, **policy)

    if args.planner:
        with ThreadPoolExecutor(max_workers=len(args.slots)) as pool:
            results = dict(zip(args.slots, pool.map(run_slot, args.slots)))
    else:
        results = {slot: run_slot(slot) for slot in args.slots}

    for slot, (accepted, stats) in results.items():
        all_stats[slot] = {
            "requested": stats.requested, "parsed": stats.parsed, "accepted": stats.accepted,
            "llm_calls": stats.llm_calls, "llm_seconds": round(stats.llm_seconds, 1),
            "rejections_by_layer": dict(stats.rejections_by_layer),
            "rounds_per_accepted": stats.rounds_per_accepted, "abandoned": stats.abandoned,
            "accepted_files": [str(c.path) for c in accepted],
            "tokens": stats.tokens.as_dict(inner.model),
        }
        if stats.catalog_overlap:
            all_stats[slot]["catalog_overlap"] = stats.catalog_overlap
        if stats.combinations:
            all_stats[slot]["combinations"] = stats.combinations
        if args.planner:
            all_stats[slot].update({"planned": stats.planned, "duplicates": stats.duplicates,
                                    "replans": stats.replans, "wall_seconds": round(stats.wall_seconds, 1)})
    total = TokenUsage()
    for s in all_stats.values():
        t = s["tokens"]
        total.add(TokenUsage(t["input_tokens"], t["output_tokens"], t.get("cached_input_tokens", 0),
                             t.get("reasoning_tokens", 0), t["calls"]))
    all_stats["_run"] = {
        "problem": pack.name, "model": inner.model, "provider": args.provider, "from_scratch": args.from_scratch,
        "catalog_diversity": args.catalog_diversity,
        "planner": args.planner, "wall_seconds": round(time.perf_counter() - t_run, 1),
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

