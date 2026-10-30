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
from native.check import bench_solutions, run_check
from native.generated import ModelCache, NativeComponent, build_components, load, parse_component, parse_response

from .client import TokenUsage
from .native_generator import NATIVE_SYSTEM_PROMPT, _compile_feedback, contract_source

UNITS = {"neighborhood": "evaluaciones de delta por segundo", "perturbation": "perturbaciones por segundo",
         "greedy_score": "construcciones greedy completas por segundo"}

TECHNIQUES = """- Evita rehacer lo que no cambia: calcula `delta` de forma INCREMENTAL, con lo que el movimiento afecta, en vez de
  evaluar la solución completa dos veces. Si eso necesita datos de la solución actual, calcúlalos una vez por solución
  y guárdalos en el componente (los esqueletos evalúan muchos movimientos de la misma solución seguidos).
- Precalcula en el constructor lo que solo depende de la instancia.
- Reutiliza memoria de trabajo propia del componente en vez de crear vectores en cada llamada; evita copiar soluciones
  salvo para devolver la nueva en `apply`/`perturb`.
- Si además tienes una aproximación mucho más barata de delta que ordena los movimientos casi como el delta exacto,
  puedes ofrecerla con `has_estimate()`/`estimate(s, m)`: la búsqueda tabú la usa para preseleccionar candidatos. No
  reemplaza a `delta`, que tiene que seguir siendo exacto.
- Mantén exactamente las mismas salidas: los mismos movimientos en el mismo orden, el mismo `apply`, el mismo `delta`
  (con tolerancia numérica), la misma perturbación con la misma semilla, los mismos puntajes. Se comparan uno por uno."""


def optimize_prompt(pack, gen: dict, comp: NativeComponent, before: float, objective_rate: float) -> str:
    spec = pack.make_model_spec()
    model = (Path(gen["dir"]) / gen["model_header"]).read_text()
    ref = (f" Como referencia, evaluar el objetivo completo de una solución cuesta lo mismo que {objective_rate:,.0f} "
           "evaluaciones por segundo." if comp.slot == "neighborhood" else "")
    return "\n".join([
        f"# Tarea\nEste componente C++ (slot `{comp.slot}`) del problema **{spec.name}** ya está validado. En una instancia "
        f"de tamaño realista hace {before:,.0f} {UNITS[comp.slot]}.{ref} Los esqueletos lo llaman cientos de miles de veces "
        "por corrida. Reescríbelo para que sea bastante más rápido SIN cambiar ninguna salida.",
        f"\n# Componente actual\n```cpp\n{comp.source}\n```",
        f"\n# Contrato\n```cpp\n{contract_source(comp.slot)}\n```",
        f"\n# El modelo C++\n```cpp\n{model}\n```",
        f"\n# Técnicas\n{TECHNIQUES}",
        "\n# Lo que se verificará\n- Las mismas salidas que el componente actual, una por una, y las validaciones del slot.\n"
        "- Al menos 1,5 veces más rápido, medido en C++.",
        f"\nDevuelve UN bloque ```cpp``` con el componente COMPLETO (misma línea COMPONENT, mismo nombre `{comp.name}`, "
        "mismos parámetros).",
    ])


def _latest(workspace: Path) -> list[NativeComponent]:
    comps = []
    for e in json.loads((workspace / "catalog.json").read_text()):
        c = parse_component(Path(e["path"]).read_text())
        c.name, c.slot, c.component, c.path = e["name"], e["slot"], dict(e["component"]), Path(e["path"])
        comps.append(c)
    return comps


def optimize_native(client, pack, workspace: str | Path, slots=("neighborhood",), rounds: int = 3,
                    min_speedup: float = 1.5, verbose: bool = True, deadline: float | None = None) -> dict:
    gen = importlib.import_module(pack.native_module).GENERATION
    ws = Path(workspace)
    tokens = TokenUsage()
    out: dict = {}
    comps = _latest(ws)
    inst, sols = bench_solutions(pack)
    for comp in [c for c in comps if c.slot in slots]:
        key = f"{comp.slot}/{comp.name}"
        if deadline is not None and time.monotonic() > deadline:
            out[key] = {"accepted": False, "skipped": "sin tiempo"}
            continue
        old_so, old_mod = build_components(gen, [comp], debug=True)
        old = load(old_so, old_mod)
        of = ModelCache(old)
        before = old.bench(of(inst), comp.slot, comp.name, {}, sols, 1.0)
        rate = old.bench_objective(of(inst), sols, 0.5)
        k = int(comp.path.stem.rsplit("_r", 1)[1])
        prompt = optimize_prompt(pack, gen, comp, before, rate)
        row = {"accepted": False, "rounds": 0, "before": round(before), "after": 0, "rejections": []}
        for rnd in range(1, rounds + 1):
            row["rounds"] = rnd
            t0 = time.perf_counter()
            text = client.complete(NATIVE_SYSTEM_PROMPT, prompt)
            used = getattr(client, "last_usage", None)
            if isinstance(used, TokenUsage):
                tokens.add(used)
            new, errors = parse_response(text)
            if not new:
                row["rejections"].append("sin bloque ```cpp``` legible: " + "; ".join(errors))
                continue
            cand = new[0]
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
                      + (f" {before:,.0f} → {res.get('after', 0):,.0f}/s" if res.get("after") else ""), flush=True)
            if res["passed"]:
                row.update(accepted=True, after=round(res["after"]), file=str(cand.path),
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
            prompt = (f"La versión optimizada fue RECHAZADA. Corrígela y devuelve el componente COMPLETO.\n\n# Reporte\n"
                      f"{res['feedback']}\n\n# Componente original (el oráculo: mismas salidas)\n```cpp\n{comp.source}\n```"
                      f"\n\n# Tu versión rechazada\n```cpp\n{cand.source}\n```\n\n# Técnicas\n{TECHNIQUES}")
        out[key] = row
    # el catálogo apunta a las versiones aceptadas
    entries = json.loads((ws / "catalog.json").read_text())
    paths = {c.name: str(c.path) for c in comps}
    for e in entries:
        e["path"] = paths.get(e["name"], e["path"])
    (ws / "catalog.json").write_text(json.dumps(entries, indent=1, ensure_ascii=False))
    out["_tokens"] = tokens.as_dict(getattr(client, "model", None))
    return out


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
    args = ap.parse_args(argv)
    client = make_client(args.provider, args.model)
    out = optimize_native(client, base_pack(args.problem), args.workspace, tuple(args.slots), args.rounds,
                          args.min_speedup, deadline=time.monotonic() + 60 * args.max_minutes)
    path = Path(args.workspace) / "optimize_stats.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "rejections"} if isinstance(v, dict) else v
                      for k, v in out.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
