"""Etapa de optimización de los componentes C++ aceptados: la misma idea que `llm/optimizer.py` en Python.

    python -m llm.native_optimizer --problem jobshop --workspace generated/jobshop_native --provider anthropic

Primero correcto, después rápido: el componente aceptado es el oráculo. Al LLM se le da el componente, el
modelo y cuánto cuesta hoy la operación que el esqueleto repite (y, como referencia, evaluar el objetivo
completo), con técnicas genéricas de optimización; nada del problema en particular. La versión nueva se
acepta si pasa las capas, da las mismas salidas que la aceptada (`native.check.optimize_check`: movimientos
y su orden, apply y delta; o la misma perturbación con la misma semilla; o las mismas construcciones) y es al
menos `min_speedup` veces más rápida, medido en C++. Queda como la ronda siguiente del mismo nombre y
`catalog.json` pasa a apuntar a ella.
"""

from __future__ import annotations

import argparse
import importlib
import json
import time
from pathlib import Path

from native.build import NativeBuildError
from native.check import bench_solutions, profile, run_check, speeds
from native.edits import EDIT_INSTRUCTIONS, EditError, merge_reply
from native.generated import ModelCache, NativeComponent, build_components, load, parse_component, parse_response

from .client import TokenUsage
from .native_generator import NATIVE_SYSTEM_PROMPT, _compile_feedback, contract_source

USAGE = """Cómo usan los esqueletos (C++) un vecindario:
- SA: elige un movimiento al azar de `moves(s)`. Según un parámetro que elige el tuner, o calcula `delta(s, m)`,
  decide con Metropolis y solo si lo acepta llama a `apply` (sin evaluar el objetivo completo), o aplica el movimiento
  y evalúa el objetivo completo del candidato. Con un `delta` incremental, la primera forma es la rápida.
- Búsqueda local de ILS y VNS: `delta` de una muestra de movimientos de `moves(s)`; aplica el mejor (o el primero que
  mejora).
- TS: `moves(s)`; si el vecindario ofrece `estimate`, lo calcula para TODOS los candidatos, los ordena y calcula
  `delta` exacto solo de los primeros (unos 5); sin `estimate`, calcula `delta` de todos.
En todos, muchos movimientos seguidos son de la MISMA solución."""

TECHNIQUES = """- Evita rehacer lo que no cambia: calcula `delta` de forma incremental, con lo que el movimiento afecta, en vez de
  evaluar la solución completa. Lo que dependa de la solución actual calcúlalo una vez por solución y guárdalo en el
  componente.
- Precalcula en el constructor lo que solo depende de la instancia; reutiliza memoria de trabajo propia en vez de
  crear vectores en cada llamada; no copies soluciones salvo para devolver la nueva en `apply`/`perturb`.
- `estimate(s, m)` (con `has_estimate()` en true) es una aproximación de delta que puede ser mucho más barata que el
  delta exacto: en TS reemplaza al delta en la revisión de todos los candidatos. Se verifica que ordene los movimientos
  como el delta exacto en la mayoría de los pares. `delta` sigue siendo exacto.
- Mantén exactamente las mismas salidas: los mismos movimientos en el mismo orden, el mismo `apply`, el mismo `delta`
  (con tolerancia numérica), la misma perturbación con la misma semilla, los mismos puntajes. Se comparan uno por uno."""


def optimize_prompt(pack, gen: dict, comp: NativeComponent, before: dict, objective_rate: float, prof: str = "",
                    siblings: list[NativeComponent] | None = None, min_speedup: float = 1.5) -> str:
    from native.check import METRICS

    spec = pack.make_model_spec()
    model = (Path(gen["dir"]) / gen["model_header"]).read_text()
    measures = "\n".join(f"- {METRICS[m]}: {v:,.0f}" for m, v in before.items())
    if comp.slot == "neighborhood":
        measures += f"\n- referencia: evaluar el objetivo completo de una solución, {objective_rate:,.0f} por segundo"
    if prof:
        measures += f"\n- perfil por método: {prof}"
    sib = [f"\n# Otro componente del mismo slot, ya optimizado en este catálogo (como referencia de lo que funcionó)\n"
           f"```cpp\n{c.source}\n```" for c in siblings or []]
    return "\n".join([
        f"# Tarea\nEste componente C++ (slot `{comp.slot}`) del problema **{spec.name}** ya está validado. Reescríbelo para "
        "que los esqueletos corran bastante más rápido con él, SIN cambiar ninguna salida.",
        f"\n# Lo que mide hoy, en una instancia de tamaño realista (en C++)\n{measures}",
        f"\n# {USAGE}" if comp.slot == "neighborhood" else "",
        f"\n# Componente actual\n```cpp\n{comp.source}\n```",
        *sib,
        f"\n# Contrato\n```cpp\n{contract_source(comp.slot)}\n```",
        f"\n# El modelo C++\n```cpp\n{model}\n```",
        f"\n# Técnicas\n{TECHNIQUES}",
        "\n# Lo que se verificará\n- Las mismas salidas que el componente actual, una por una, y las validaciones del slot.\n"
        f"- Que alguna de las medidas de arriba mejore al menos {min_speedup:g} veces y ninguna empeore más de un 10 %.",
        f"\n# Formato de la respuesta\n{EDIT_INSTRUCTIONS}\nLa línea COMPONENT, el nombre `{comp.name}` y los parámetros no "
        "cambian.",
    ])


def _latest(workspace: Path) -> list[NativeComponent]:
    comps = []
    for e in json.loads((workspace / "catalog.json").read_text()):
        c = parse_component(Path(e["path"]).read_text())
        c.name, c.slot, c.component, c.path = e["name"], e["slot"], dict(e["component"]), Path(e["path"])
        comps.append(c)
    return comps


def _round(path: Path) -> int:
    return int(path.stem.rsplit("_r", 1)[1])


def _siblings(comps: list[NativeComponent], comp: NativeComponent, k: int = 2) -> list[NativeComponent]:
    """Los otros componentes del mismo slot que ya pasaron por una optimización (ronda > 1), los más recientes."""
    done = [c for c in comps if c.slot == comp.slot and c.name != comp.name and _round(c.path) > 1]
    return sorted(done, key=lambda c: -_round(c.path))[:k]


def optimize_one(client, pack, gen: dict, ws: Path, comp: NativeComponent, comps: list[NativeComponent], inst, sols,
                 rounds: int, min_speedup: float, tokens: TokenUsage, verbose: bool) -> dict:
    """Una pasada sobre un componente: hasta `rounds` intentos (el primero y las correcciones)."""
    old_so, old_mod = build_components(gen, [comp], debug=True)
    old = load(old_so, old_mod)
    of = ModelCache(old)
    before = speeds(old, of, comp.slot, comp.name, inst, sols)
    rate = old.bench_objective(of(inst), sols, 0.5)
    prof = profile(old, of, comp.slot, comp.name, inst, sols)
    k = _round(comp.path)
    prompt = optimize_prompt(pack, gen, comp, before, rate, prof, _siblings(comps, comp), min_speedup)
    base = comp.source  # sobre lo que se aplican las ediciones de la próxima respuesta
    key = f"{comp.slot}/{comp.name}"
    row = {"accepted": False, "rounds": 0, "before": {m: round(v) for m, v in before.items()}, "after": {},
           "min_speedup": min_speedup, "rejections": []}
    for rnd in range(1, rounds + 1):
        row["rounds"] = rnd
        t0 = time.perf_counter()
        text = client.complete(NATIVE_SYSTEM_PROMPT, prompt)
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        # ediciones sobre el componente actual (primer intento) o sobre la versión rechazada (correcciones)
        try:
            merged = merge_reply(base, text)
            cand = parse_component(merged.source)
        except (EditError, ValueError) as exc:
            row["rejections"].append(f"respuesta inaplicable: {exc}")
            row["edit_failures"] = row.get("edit_failures", 0) + 1
            prompt = (f"Tu respuesta no se pudo aplicar: {exc}.\n\n{EDIT_INSTRUCTIONS}\n\n# Código sobre el que se "
                      f"aplican las ediciones\n```cpp\n{base}\n```")
            continue
        row.setdefault("reply_modes", []).append(merged.mode)
        cand.name, cand.slot, cand.component = comp.name, comp.slot, dict(comp.component)
        cand.path = comp.path.with_name(f"{comp.name}_r{k + rnd}.hpp")
        cand.path.write_text(cand.source)
        try:
            so, mod = build_components(gen, [cand], debug=True)
            res = run_check({"mode": "optimize", "problem": pack.name, "old_so": str(old_so), "old_module": old_mod,
                             "so": str(so), "module": mod, "candidate": comp.name, "component": comp.component,
                             "min_speedup": min_speedup, "out_dir": str(ws / comp.slot)})
        except NativeBuildError as exc:
            res = {"passed": False, "failed_layer": "compile", "feedback": _compile_feedback(str(exc), comp.name)}
        if verbose:
            print(f"[optimizar/{key}] ronda {rnd} ({time.perf_counter() - t0:.0f}s): "
                  + ("✔" if res["passed"] else f"✘ {res['failed_layer']}")
                  + "".join(f" {m} {before[m]:,.0f}→{res['after'].get(m, 0):,.0f}" for m in before if res.get("after")),
                  flush=True)
        if res["passed"]:
            row.update(accepted=True, after={m: round(v) for m, v in res["after"].items()},
                       estimate="has_estimate" in cand.source)
            for j in range(1, rnd):  # las rondas rechazadas no quedan como la más alta
                comp.path.with_name(f"{comp.name}_r{k + j}.hpp").unlink(missing_ok=True)
            if rnd > 1:
                cand.path = cand.path.rename(comp.path.with_name(f"{comp.name}_r{k + 1}.hpp"))
            row["file"] = str(cand.path)
            comp.path, comp.source = cand.path, cand.source
            break
        row["rejections"].append(res["feedback"][-3000:])
        cand.path.unlink(missing_ok=True)
        base = cand.source
        prompt = (f"La versión optimizada fue RECHAZADA. Corrígela.\n\n# Reporte\n{res['feedback']}\n\n# Componente "
                  f"original (el oráculo: mismas salidas)\n```cpp\n{comp.source}\n```\n\n# Tu versión rechazada (las "
                  f"ediciones se aplican sobre ella)\n```cpp\n{cand.source}\n```\n\n# Técnicas\n{TECHNIQUES}\n\n"
                  f"# Formato de la respuesta\n{EDIT_INSTRUCTIONS}")
    return row


def optimize_native(client, pack, workspace: str | Path, slots=("neighborhood",), rounds: int = 3,
                    min_speedup: float = 1.5, verbose: bool = True, deadline: float | None = None,
                    passes: int = 1, later_speedup: float = 1.2) -> dict:
    """Pasadas encadenadas: en cada una, los componentes que mejoraron en la anterior se vuelven a optimizar con su
    versión nueva como oráculo (pidiendo `later_speedup` en vez de `min_speedup`); el resto ya no. Los componentes del
    mismo slot que ya se optimizaron se muestran como referencia."""
    gen = importlib.import_module(pack.native_module).GENERATION
    ws = Path(workspace)
    tokens = TokenUsage()
    out: dict = {}
    comps = _latest(ws)
    inst, sols = bench_solutions(pack)
    active = [c for c in comps if c.slot in slots]
    for p in range(1, passes + 1):
        if not active:
            break
        improved = []
        for comp in active:
            key = f"{comp.slot}/{comp.name}" + (f"#{p}" if passes > 1 else "")
            if deadline is not None and time.monotonic() > deadline:
                out[key] = {"accepted": False, "skipped": "sin tiempo"}
                continue
            out[key] = optimize_one(client, pack, gen, ws, comp, comps, inst, sols, rounds,
                                    min_speedup if p == 1 else later_speedup, tokens, verbose)
            if out[key]["accepted"]:
                improved.append(comp)
            _write_catalog(ws, comps)  # a medida que avanza: un job cortado no pierde lo aceptado
        active = improved
    out["_tokens"] = tokens.as_dict(getattr(client, "model", None))
    return out


def _write_catalog(ws: Path, comps: list[NativeComponent]) -> None:
    entries = json.loads((ws / "catalog.json").read_text())
    paths = {c.name: str(c.path) for c in comps}
    for e in entries:
        e["path"] = paths.get(e["name"], e["path"])
    (ws / "catalog.json").write_text(json.dumps(entries, indent=1, ensure_ascii=False))


def main(argv: list[str] | None = None) -> None:
    from .client import make_client
    from .cycle import base_pack

    ap = argparse.ArgumentParser(prog="python -m llm.native_optimizer")
    ap.add_argument("--problem", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--slots", nargs="+", default=["neighborhood"])
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--min-speedup", type=float, default=1.5)
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-minutes", type=float, default=40.0)
    ap.add_argument("--passes", type=int, default=3, help="pasadas encadenadas (los que mejoran vuelven a optimizarse)")
    ap.add_argument("--later-speedup", type=float, default=1.2, help="mejora exigida desde la segunda pasada")
    args = ap.parse_args(argv)
    client = make_client(args.provider, args.model)
    out = optimize_native(client, base_pack(args.problem), args.workspace, tuple(args.slots), args.rounds,
                          args.min_speedup, deadline=time.monotonic() + 60 * args.max_minutes, passes=args.passes,
                          later_speedup=args.later_speedup)
    path = Path(args.workspace) / "optimize_stats.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "rejections"} if isinstance(v, dict) else v
                      for k, v in out.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
