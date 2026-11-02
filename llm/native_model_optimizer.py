"""Etapa de optimización del MODELO C++ (el que escribió el LLM, `llm.native_model_generator`), como la de los
componentes (`llm.native_optimizer`): el modelo aceptado es el oráculo.

    python -m llm.native_model_optimizer --problem clsp --workspace generated/clsp_native --provider anthropic

La versión nueva tiene que pasar los chequeos del modelo, dar las mismas salidas que la aceptada (violaciones, costo,
objetivo y factibilidad, también en soluciones rotas) y ser más rápida, medido en C++: evaluaciones del objetivo por
segundo y pasos de trayectoria de los vecindarios del catálogo (que lo usan de verdad). Los componentes se compilan con
la versión nueva, así que los miembros del modelo que usan tienen que seguir existiendo con el mismo significado.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from pathlib import Path

from native.build import NativeBuildError
from native.check_model import MODEL_METRICS, run_model_check
from native.edits import EDIT_INSTRUCTIONS, EditError, merge_reply
from native.generated import build_components, parse_component
from native.generic_model import generation

from .client import TokenUsage
from .native_model_generator import MODEL_SYSTEM_PROMPT, _compile_feedback, contract_text

TECHNIQUES = """- Precalcula en `parse` lo que solo depende de la instancia; guarda memoria de trabajo `mutable` en vez de crear vectores
  en cada llamada.
- Los componentes evalúan muchas soluciones seguidas que difieren poco de la anterior (un movimiento): si evaluar es caro,
  puedes recordar la última solución evaluada con lo que calculaste y, si la nueva difiere en poco, rehacer solo lo
  afectado (comparándola con la guardada). El resultado tiene que ser exactamente el mismo.
- Si resuelves un subproblema de optimización, aprovecha su estructura (p.ej. se descompone, o cambia poco entre
  soluciones vecinas), pero sigue siendo EXACTO.
- Mantén exactamente las mismas salidas: violaciones, costo, objetivo, factibilidad y la solución trivial."""


def _used_members(model_src: str, comps: list) -> list[str]:
    """Los miembros del modelo que nombran los componentes (`algo.miembro`): no pueden desaparecer."""
    declared = set(re.findall(r"\b([A-Za-z_]\w*)\s*(?:\(|;|=|\[|\{)", model_src))
    used = set()
    for c in comps:
        used |= set(re.findall(r"\.\s*([A-Za-z_]\w*)", c.source))
    return sorted(used & declared - {"size", "push_back", "begin", "end", "resize", "assign", "clear", "back", "empty",
                                     "insert", "erase", "data", "first", "second", "reserve", "swap", "front", "count"})


def optimize_prompt(spec, source: str, before: dict, members: list[str], min_speedup: float) -> str:
    from native.check import thresholds

    need = thresholds(before, min_speedup)
    measures = "\n".join(f"- {MODEL_METRICS[k]}: {v:,.0f} (para aceptar: {need[k]:g}×)" for k, v in before.items())
    return "\n".join([
        f"# Tarea\nEste modelo C++ del problema **{spec.name}** ya está validado. Reescríbelo para que sea bastante más "
        "rápido, SIN cambiar ninguna salida.",
        f"\n# Lo que mide hoy, en una instancia de tamaño realista\n{measures}",
        f"\n# Modelo actual\n```cpp\n{source}\n```",
        f"\n# Contrato\n```cpp\n{contract_text()}\n```",
        ("\n# Miembros que usan los componentes del catálogo (tienen que seguir existiendo, con el mismo significado)\n"
         + ", ".join(f"`{m}`" for m in members)) if members else "",
        f"\n# Técnicas\n{TECHNIQUES}",
        "\n# Lo que se verificará\n- Los casos del problema, las mismas salidas que el modelo actual una por una y la "
        "coherencia entre métodos.\n- Que alguna medida mejore lo indicado junto a ella y ninguna empeore más de un 10 %.",
        f"\n# Formato de la respuesta\n{EDIT_INSTRUCTIONS}",
    ])


def optimize_model(client, pack, workspace: str | Path, rounds: int = 3, min_speedup: float = 1.5, passes: int = 2,
                   later_speedup: float = 1.2, verbose: bool = True) -> dict:
    mip_parts = pack.variants[next(iter(pack.variants))][1] if pack.variants else f"{pack.module}.model_parts"
    ws = Path(workspace)
    model_dir = ws / "model"
    gen = generation(model_dir, mip_parts)
    comps = []
    if (ws / "catalog.json").exists():
        for e in json.loads((ws / "catalog.json").read_text()):
            c = parse_component(Path(e["path"]).read_text())
            c.name, c.slot, c.component = e["name"], e["slot"], dict(e["component"])
            comps.append(c)
    nbhs = [c.name for c in comps if c.slot == "neighborhood"]
    spec = pack.make_model_spec()
    tokens = TokenUsage()
    out = {"passes": []}
    accepted_src = (model_dir / "model.hpp").read_text()
    k = len(list(model_dir.glob("model_opt*.hpp")))
    for p in range(1, passes + 1):
        need = min_speedup if p == 1 else later_speedup
        # el aceptado, compilado en su propio directorio (los dos modelos se llaman model.hpp)
        old_dir = model_dir / "_accepted"
        old_dir.mkdir(exist_ok=True)
        (old_dir / "model.hpp").write_text(accepted_src)
        old_gen = generation(old_dir, mip_parts)
        old_so, old_mod = build_components(old_gen, comps, debug=True)
        before = None
        row = {"pass": p, "accepted": False, "rounds": 0, "rejections": [], "reply_modes": []}
        base, prompt = accepted_src, None
        for rnd in range(1, rounds + 1):
            row["rounds"] = rnd
            if prompt is None:
                from native.check_model import model_speeds  # medido en este proceso: una sola vez por pasada
                from native.generated import load

                import importlib
                ref = importlib.import_module(mip_parts)
                before = model_speeds(load(old_so, old_mod), ref, pack, nbhs)
                row["before"] = {m: round(v) for m, v in before.items()}
                prompt = optimize_prompt(spec, accepted_src, before, _used_members(accepted_src, comps), need)
            text = client.complete(MODEL_SYSTEM_PROMPT, prompt)
            used = getattr(client, "last_usage", None)
            if isinstance(used, TokenUsage):
                tokens.add(used)
            try:
                merged = merge_reply(base, text)
            except EditError as exc:
                row["rejections"].append(f"respuesta inaplicable: {exc}")
                prompt = f"Tu respuesta no se pudo aplicar: {exc}.\n\n{EDIT_INSTRUCTIONS}\n\n# Código\n```cpp\n{base}\n```"
                continue
            row["reply_modes"].append(merged.mode)
            cand = merged.source
            k += 1
            (model_dir / f"model_opt{k}.hpp").write_text(cand)
            new_dir = model_dir / "_candidate"
            new_dir.mkdir(exist_ok=True)
            (new_dir / "model.hpp").write_text(cand)
            try:
                so, mod = build_components(generation(new_dir, mip_parts), comps, debug=True)
                res = run_model_check({"mode": "optimize", "problem": pack.name, "old_so": str(old_so), "old_module": old_mod,
                                       "so": str(so), "module": mod, "mip_parts": mip_parts, "neighborhoods": nbhs,
                                       "min_speedup": need, "out_dir": str(new_dir)})
            except NativeBuildError as exc:
                res = {"passed": False, "failed_layer": "compile", "feedback": _compile_feedback(str(exc))}
            if verbose:
                print(f"[optimizar modelo] pasada {p}, ronda {rnd}: " + ("✔ " if res["passed"] else f"✘ {res['failed_layer']} ")
                      + res["feedback"][:300], flush=True)
            if res["passed"]:
                row.update(accepted=True, after={m: round(v) for m, v in res["after"].items()}, file=f"model_opt{k}.hpp")
                accepted_src = cand
                (model_dir / "model.hpp").write_text(cand)
                break
            row["rejections"].append(f"[{res['failed_layer']}] {res['feedback'][-2500:]}")
            base = cand
            prompt = (f"La versión optimizada fue RECHAZADA. Corrígela.\n\n# Reporte\n{res['feedback']}\n\n# Modelo aceptado "
                      f"(el oráculo: mismas salidas)\n```cpp\n{accepted_src}\n```\n\n# Tu versión rechazada (las ediciones se "
                      f"aplican sobre ella)\n```cpp\n{cand}\n```\n\n# Técnicas\n{TECHNIQUES}\n\n# Formato de la respuesta\n"
                      f"{EDIT_INSTRUCTIONS}")
        out["passes"].append(row)
        if not row["accepted"]:
            break
    for d in ("_accepted", "_candidate"):
        shutil.rmtree(model_dir / d, ignore_errors=True)
    out["_tokens"] = tokens.as_dict(getattr(client, "model", None))
    (ws / "model_optimize_stats.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out


def main(argv: list[str] | None = None) -> None:
    from .client import make_client
    from .cycle import base_pack

    ap = argparse.ArgumentParser(prog="python -m llm.native_model_optimizer")
    ap.add_argument("--problem", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default=None)
    args = ap.parse_args(argv)
    t0 = time.perf_counter()
    out = optimize_model(make_client(args.provider, args.model), base_pack(args.problem), args.workspace, args.rounds,
                         passes=args.passes)
    out["wall_seconds"] = round(time.perf_counter() - t0, 1)
    print(json.dumps({k: v for k, v in out.items()}, indent=2, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
