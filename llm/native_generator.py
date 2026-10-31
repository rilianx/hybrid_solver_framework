"""Componentes en C++ generados por el LLM: generar → compilar → validar → corregir.

    python -m llm.native_generator --problem jobshop --workspace generated/jobshop_native \\
        --slots greedy_score neighborhood perturbation --n 3 --rounds 3 --provider anthropic

Lo que ve el LLM es lo mismo que en Python, nada específico de cómo resolver el problema: la descripción,
el header del MODELO C++ (evaluación, plan, vista constructiva; no el catálogo escrito a mano ni sus
helpers), el contrato del slot en C++ y las reglas genéricas (delta exacto, soluciones inmutables, que
los métodos se llaman cientos de miles de veces por segundo). Qué vecindarios usar, cómo evaluarlos o si
conviene estimar es cosa suya.

Cada candidato se compila con los aceptados del mismo slot (un error de compilación vuelve al LLM con la
salida del compilador) y se valida en un subproceso (`native.check`) con las capas de Python; una caída
es un rechazo. Lo aceptado queda en `<workspace>/<slot>/<nombre>_r<ronda>.hpp` y `catalog.json`.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from native.build import INCLUDE, NativeBuildError
from native.check import NATIVE_SKELETONS_FOR_SLOT, run_check
from native.edits import EDIT_INSTRUCTIONS, EditError, merge_reply
from native.generated import SLOT_BASE, NativeComponent, build_components, parse_component, parse_response

from .client import TokenUsage

NATIVE_SYSTEM_PROMPT = """Eres un experto en metaheurísticas que escribe componentes algorítmicos en C++17 para un framework de
solvers híbridos. Escribes la pieza que se te pide, correcta y eficiente; el bucle del algoritmo (los esqueletos SA, ILS,
VNS, TS, PR) es del framework.

Reglas de todo componente:
1. Un bloque ```cpp``` por componente. La PRIMERA línea es `// COMPONENT: {"name": "<snake_case único>", "slot": "<slot>",
   "params": {...}}` (JSON en una línea; cada parámetro con "type" ("int" | "float" | "cat") y "range" [min, max] o
   "values" [...]; el tuner los afina).
2. Una clase que hereda de la interfaz del slot (`hsf::<Interfaz><Modelo>`) e implementa todos sus métodos virtuales puros.
3. Una función `make_component(const <Modelo>& model, const hsf::Config& params)` que devuelve
   `std::unique_ptr<hsf::<Interfaz><Modelo>>`. Lee los parámetros con `params.get("nombre", valor_por_defecto)`
   (números) o `params.text("nombre", "defecto")`, con defaults dentro de los rangos declarados.
4. Sin `#include` (la biblioteca estándar usual ya está incluida: algorithm, vector, map, set, unordered_map, deque,
   queue, numeric, cmath, limits, random, functional, memory) ni `using namespace std`. Sin I/O ni variables globales
   mutables. Puedes definir clases y funciones auxiliares en el mismo bloque. Cada bloque se compila en su propio
   espacio de nombres, con `using namespace` del problema y `hsf::Move`, `hsf::Rng`, `hsf::Config` visibles.
5. Toda aleatoriedad sale del `Rng& rng` que recibe el método (`rng.uniform()`, `rng.below(n)`, `rng.g`).
6. Las soluciones son inmutables: `apply`/`perturb` devuelven una solución nueva sin modificar la que reciben.
7. El objetivo se MINIMIZA. El modelo es `const`; guarda una referencia a él en tu clase.
8. Los esqueletos llaman a estos métodos cientos de miles de veces por segundo, con presupuestos de segundos: la
   eficiencia es parte de la calidad del componente. Puedes guardar en la clase memoria de trabajo propia (un
   componente lo usa una sola corrida, en un solo hilo).

Formato de salida: los bloques ```cpp``` pedidos, cada uno con una línea breve antes. Nada más."""

SLOT_HINTS = {
    "neighborhood": (
        "Un movimiento es un `hsf::Move` (6 enteros; los que no uses, en 0). Se verificará: `delta(s, m)` es EXACTAMENTE "
        "`model.objective(apply(s, m)) - model.objective(s)` (puedes calcularlo así si no tienes algo más rápido y exacto); "
        "`moves(s, out)` agrega movimientos a `out` y no queda vacío; algún movimiento MEJORA la solución de partida; y el "
        "operador es una idea distinta de los otros vecindarios aceptados. Métodos opcionales: `tabu_key(m)` (lo que la "
        "búsqueda tabú prohíbe tras aplicar m; por defecto el mismo movimiento) y `has_estimate()`/`estimate(s, m)` (una "
        "aproximación barata de delta para preseleccionar candidatos; se verifica que ordene los movimientos parecido a "
        "delta)."
    ),
    "perturbation": "Se verificará: `perturb(s, strength, rng)` devuelve una solución distinta de `s` y factible (strength >= 1).",
    "greedy_score": (
        "Escribes SOLO el criterio de un constructor greedy: `score(partial, action)` devuelve un número, MENOR es mejor. El "
        "bucle, la regla (greedy, lista restringida o ruleta) y la factibilidad son del framework: los candidatos ya vienen "
        "filtrados. Se llama para cada candidato en cada paso, así que debe ser barato y no modificar `partial`. Se "
        "verificará que el constructor que arma produce soluciones factibles y no mucho peores que la de referencia."
    ),
    "constructor": "Se verificará: `build(rng)` devuelve una solución FACTIBLE y es determinista dada la semilla.",
    "relink": (
        "Conectas dos soluciones para el esqueleto PR (path relinking): `distance(a, b)` dice cuántos pasos las separan y "
        "`step(cur, guide, rng)` da una solución más cerca de `guide`. PR mantiene una población de soluciones buenas; "
        "elige dos, recorre el camino de una a la otra (en cada paso llama varias veces a `step` y se queda con la de mejor "
        "objetivo), mejora con búsqueda tabú la mejor solución del tramo central del camino y la pone en la población en "
        "lugar de la peor. `distance` también se usa para no repetir soluciones en la población. Un paso puede dar una "
        "solución infactible (el objetivo la penaliza). Se verificará: `distance(a, a) == 0`, simétrica y mayor que 0 entre "
        "soluciones distintas; cada `step` baja la distancia a la guía estrictamente, y con distancia 0 la solución es la "
        "guía."
    ),
}


def _block(source: str, start: int) -> str:
    """Desde `start` hasta la llave que cierra el primer bloque (incluido el `;` de un struct)."""
    i, depth = source.index("{", start), 0
    for j in range(i, len(source)):
        depth += {"{": 1, "}": -1}.get(source[j], 0)
        if depth == 0:
            end = j + 1
            return source[start:end + (1 if source[end:end + 1] == ";" else 0)]
    raise ValueError("llaves desbalanceadas")


def contract_source(slot: str) -> str:
    """El contrato del slot en C++, tal cual está en `native/include/hsf/core.hpp`, con Move, Rng y Config."""
    core = (INCLUDE / "hsf" / "core.hpp").read_text()
    parts = [core[core.index("using Move"):core.index("\n", core.index("using Move")) + 1]]
    for name in ("struct Rng", "struct Config"):
        parts.append(_block(core, core.index(name)))
    m = re.search(r"template <class M>\nstruct " + SLOT_BASE[slot] + r" \{", core)
    parts.append(_block(core, m.start()))
    return "\n\n".join(parts)


def _model_type(gen: dict) -> str:
    return gen["model_type"].split("::")[-1]


def generation_prompt(pack, gen: dict, slot: str, n: int, avoid: list[str]) -> str:
    spec = pack.make_model_spec()
    model = (Path(gen["dir"]) / gen["model_header"]).read_text()
    T = _model_type(gen)
    parts = [
        f"# Tarea\nGenera {n} componentes ESTRUCTURALMENTE DISTINTOS para el slot `{slot}` del problema de abajo, en C++.",
        "Distintos significa ideas algorítmicas diferentes (no el mismo operador con otro parámetro). Nombra cada uno de forma "
        f"descriptiva. La interfaz es `hsf::{SLOT_BASE[slot]}<{T}>` y la fábrica devuelve `std::unique_ptr<hsf::{SLOT_BASE[slot]}<{T}>>`.",
        f"\n# Contrato (de native/include/hsf/core.hpp)\n```cpp\n{contract_source(slot)}\n```",
        "\n# Qué se verificará\n" + SLOT_HINTS.get(slot, ""),
        f"\n# Problema: {spec.name}\n{spec.description}",
        f"\n## El modelo C++ (`{gen['model_type']}`; tu componente recibe una referencia const a él)\n```cpp\n{model}\n```",
    ]
    if avoid:
        parts.append(f"\nYa existen componentes llamados {avoid} en este slot; usa ideas y nombres distintos.")
    parts.append(f"\nDevuelve exactamente {n} bloques ```cpp```.")
    return "\n".join(parts)


def correction_prompt(gen: dict, slot: str, comp: NativeComponent, feedback: str) -> str:
    return "\n".join([
        f"El siguiente componente C++ para el slot `{slot}` fue RECHAZADO. Corrígelo manteniendo la misma idea y el mismo "
        f"nombre (`{comp.name}`).",
        "Arregla lo que el reporte señala sin romper lo que ya funcionaba.",
        f"\n# Reporte\n{feedback}",
        f"\n# Contrato\n```cpp\n{contract_source(slot)}\n```",
        f"\n# Componente rechazado (las ediciones se aplican sobre él)\n```cpp\n{comp.source}\n```",
        f"\n# Formato de la respuesta\n{EDIT_INSTRUCTIONS}",
    ])


@dataclass
class NativeStats:
    slot: str
    requested: int = 0
    parsed: int = 0
    accepted: int = 0
    llm_calls: int = 0
    llm_seconds: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    rejections_by_layer: Counter = field(default_factory=Counter)
    rounds_per_accepted: dict = field(default_factory=dict)
    abandoned: list = field(default_factory=list)
    edits: int = 0  # correcciones devueltas como ediciones (no el componente completo)

    def as_dict(self, model: str | None, accepted: list[NativeComponent]) -> dict:
        return {"requested": self.requested, "parsed": self.parsed, "accepted": self.accepted, "llm_calls": self.llm_calls,
                "llm_seconds": round(self.llm_seconds, 1), "rejections_by_layer": dict(self.rejections_by_layer),
                "rounds_per_accepted": self.rounds_per_accepted, "abandoned": self.abandoned, "patches": self.edits,
                "accepted_files": [str(c.path) for c in accepted], "tokens": self.tokens.as_dict(model)}


def _compile_feedback(err: str, name: str) -> str:
    """La salida del compilador, con lo que toca al componente (`<nombre>.hpp:<línea>`) primero."""
    lines = err.splitlines()
    own = [ln for ln in lines if f"{name}.hpp:" in ln and ("error" in ln or "note" in ln)]
    return ("No compila. Errores en tu componente (líneas del bloque, contando desde la línea COMPONENT = 1):\n"
            + "\n".join(own[:40] or lines[-40:]))


def generate_native_slot(client, pack, slot: str, n: int, workspace: str | Path, max_rounds: int = 3,
                         verbose: bool = True) -> tuple[list[NativeComponent], NativeStats]:
    gen = importlib.import_module(pack.native_module).GENERATION
    ws = Path(workspace)
    (ws / slot).mkdir(parents=True, exist_ok=True)
    stats = NativeStats(slot=slot, requested=n)
    accepted: list[NativeComponent] = []

    def ask(prompt: str) -> str:
        t0 = time.perf_counter()
        text = client.complete(NATIVE_SYSTEM_PROMPT, prompt)
        stats.llm_calls += 1
        stats.llm_seconds += time.perf_counter() - t0
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            stats.tokens.add(used)
        return text

    comps, errors = parse_response(ask(generation_prompt(pack, gen, slot, n, [])))
    comps = [c for c in comps if c.slot == slot]
    stats.parsed = len(comps)
    if verbose:
        print(f"[{slot}] ronda 1: {len(comps)} componentes" + (f"; sin leer: {errors}" if errors else ""))
    pending = [(c, 1) for c in comps]
    while pending:
        comp, rnd = pending.pop(0)
        comp.path = ws / slot / f"{comp.name}_r{rnd}.hpp"
        comp.path.write_text(comp.source)
        same = [c for c in accepted if c.slot == slot]
        try:
            so, module = build_components(gen, same + [comp], debug=True)
            result = run_check({"problem": pack.name, "so": str(so), "module": module, "candidate": comp.name,
                                "component": comp.component, "peers": [c.name for c in same], "out_dir": str(ws / slot)})
        except NativeBuildError as exc:
            result = {"passed": False, "failed_layer": "compile", "feedback": _compile_feedback(str(exc), comp.name)}
        if result["passed"]:
            comp.component = result["component"]
            accepted.append(comp)
            stats.accepted += 1
            stats.rounds_per_accepted[comp.name] = rnd
            if verbose:
                print(f"[{slot}] ✔ {comp.name} aceptado (ronda {rnd})")
            continue
        stats.rejections_by_layer[result["failed_layer"] or "?"] += 1
        if verbose:
            print(f"[{slot}] ✘ {comp.name} rechazado en '{result['failed_layer']}' (ronda {rnd})")
        if rnd >= max_rounds:
            stats.abandoned.append(comp.name)
            continue
        prompt = correction_prompt(gen, slot, comp, result["feedback"])
        for _attempt in range(2):  # una edición que no aplica vuelve en el momento, con el motivo
            try:
                merged = merge_reply(comp.source, ask(prompt))
                f = parse_component(merged.source)
                break
            except (EditError, ValueError) as exc:
                stats.rejections_by_layer["edit"] += 1
                prompt = (f"Tu respuesta no se pudo aplicar: {exc}.\n\n{EDIT_INSTRUCTIONS}\n\n# Código sobre el que se "
                          f"aplican las ediciones\n```cpp\n{comp.source}\n```")
        else:
            stats.abandoned.append(comp.name)
            continue
        stats.edits += merged.mode == "edits"
        f.name, f.slot = comp.name, slot  # misma idea y nombre
        f.component.update({"name": comp.name, "slot": slot})
        pending.append((f, rnd + 1))
    return accepted, stats


def write_catalog(workspace: str | Path, accepted: list[NativeComponent]) -> Path:
    """`catalog.json`: los aceptados de todos los slots (los que carga el tuner)."""
    ws = Path(workspace)
    path = ws / "catalog.json"
    old = json.loads(path.read_text()) if path.exists() else []
    names = {c.name for c in accepted}
    entries = [e for e in old if e["name"] not in names] + [
        {"name": c.name, "slot": c.slot, "path": str(c.path), "component": c.component} for c in accepted]
    path.write_text(json.dumps(entries, indent=1, ensure_ascii=False))
    return path


def main(argv: list[str] | None = None) -> None:
    from .client import make_client
    from .cycle import base_pack

    ap = argparse.ArgumentParser(prog="python -m llm.native_generator")
    ap.add_argument("--problem", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--slots", nargs="+", default=["greedy_score", "neighborhood", "perturbation"])
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default=None)
    args = ap.parse_args(argv)

    pack = base_pack(args.problem)
    client = make_client(args.provider, args.model)
    t0 = time.perf_counter()
    all_stats, every = {}, []
    for slot in args.slots:
        accepted, stats = generate_native_slot(client, pack, slot, args.n, args.workspace, args.rounds)
        every += accepted
        all_stats[slot] = stats.as_dict(client.model, accepted)
        write_catalog(args.workspace, accepted)
    total = TokenUsage()
    for s in all_stats.values():
        t = s["tokens"]
        total.add(TokenUsage(t["input_tokens"], t["output_tokens"], t.get("cached_input_tokens", 0),
                             t.get("reasoning_tokens", 0), t["calls"]))
    all_stats["_run"] = {"problem": args.problem, "model": client.model, "provider": args.provider, "language": "cpp",
                         "from_scratch": True, "wall_seconds": round(time.perf_counter() - t0, 1),
                         "tokens": total.as_dict(client.model)}
    out = Path(args.workspace) / "stats.json"
    if out.exists():  # un slot nuevo sobre un catálogo existente: no se pisan las estadísticas de la corrida anterior
        out = out.with_name(f"stats_{'_'.join(args.slots)}.json")
    out.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False))
    print(f"{len(every)} componentes C++ aceptados; resumen en {out}")


def load_native_catalog(pack, workspace: str | Path):
    """El módulo compilado con los aceptados de un workspace y sus entradas para el registro de Python:
    (módulo nativo, model_of, [(COMPONENT, fábrica)])."""
    from native.generated import ModelCache, build_components, factory, load, parse_component

    gen = importlib.import_module(pack.native_module).GENERATION
    entries = json.loads((Path(workspace) / "catalog.json").read_text())
    comps = []
    for e in entries:
        c = parse_component(Path(e["path"]).read_text())
        c.name, c.slot, c.component = e["name"], e["slot"], dict(e["component"])
        comps.append(c)
    so, name = build_components(gen, comps)
    mod = load(so, name)
    model_of = ModelCache(mod)
    out = []
    for c in comps:
        comp = dict(c.component)
        comp["compatible_skeletons"] = NATIVE_SKELETONS_FOR_SLOT[c.slot]  # los esqueletos nativos de hoy (p.ej. PR)
        out.append((comp, factory(mod, model_of, c.slot, c.name)))
    return mod, model_of, out


if __name__ == "__main__":
    main()
