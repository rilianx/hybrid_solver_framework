"""El MODELO de un problema en C++, escrito por el LLM: generar → compilar → validar → corregir.

    python -m llm.native_model_generator --problem clsp --workspace generated/clsp_native --provider anthropic

Lo que ve el LLM: la descripción del problema, la clase de la instancia (su formato de entrada), el formato de la
respuesta, los nombres de las familias de restricciones y de los términos del costo, el contrato del modelo C++
(`native/include/hsf/generic.hpp`) y los casos visibles. No ve ningún modelo escrito a mano. El modelo se compila con
los bindings genéricos y se valida en un subproceso (`native.check_model`) contra los casos visibles y ocultos, casos
ocultos generados y la coherencia entre sus métodos; los errores vuelven al LLM. Lo aceptado queda en
`<workspace>/model/model.hpp`, y sobre él se generan los componentes (`llm.native_generator`).
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from native.build import INCLUDE, NativeBuildError
from native.check_model import run_model_check
from native.edits import EDIT_INSTRUCTIONS, EditError, merge_reply
from native.generated import _BLOCK, build_components
from native.generic_model import generation

from . import outline
from .client import TokenUsage

MODEL_SYSTEM_PROMPT = """Eres un experto en optimización combinatoria que escribe en C++17 el MODELO de un problema para un framework
de solvers híbridos: cómo leer una instancia, cómo es una solución, qué restricciones viola y cuánto cuesta. Los
componentes heurísticos (vecindarios, perturbaciones, ...) y los algoritmos se escriben después, sobre tu modelo.

Reglas:
1. Un solo bloque ```cpp``` con el archivo `model.hpp` completo: `#pragma once`, `#include <hsf/core.hpp>` y los headers
   estándar que uses. Todo dentro de `namespace gen`, en una `struct Model` que cumple el contrato.
2. Solo la biblioteca estándar. Si el costo o las violaciones de una solución dependen de resolver un subproblema de
   optimización, impleméntalo tú y de forma EXACTA: los casos de prueba lo verifican.
3. Sin I/O ni variables globales mutables. Puedes guardar memoria de trabajo en miembros `mutable` (un modelo se usa en
   un solo hilo).
4. `objective` y `feasible` se llaman cientos de miles de veces por segundo: precalcula en `parse` lo que dependa solo
   de la instancia y no reserves memoria en cada llamada si puedes evitarlo.
5. Usa exactamente los nombres de familias y términos indicados.

Formato de salida: el bloque ```cpp```, con una línea breve antes. Nada más."""


def contract_text() -> str:
    head = (INCLUDE / "hsf" / "generic.hpp").read_text()
    contract = head[:head.index("#pragma once")].strip()
    from .native_generator import rng_config_definitions

    core = (INCLUDE / "hsf" / "core.hpp").read_text()
    rng = core[core.index("struct Rng"):core.index("};", core.index("struct Rng")) + 2]
    if not outline.compact_default():
        defs = rng_config_definitions(core)
        rng += "\n" + "\n".join(line for line in defs.splitlines() if line.startswith("inline") and "Rng::" in line)
    return f"{contract}\n\n// en <hsf/core.hpp>:\nnamespace hsf {{\n{rng}\n}}"


def _cases_block(cases) -> str:
    """Los casos visibles con sus respuestas (factible/infactible, costo, familias violadas)."""
    visible = [c for c in cases if c.visible]
    if not visible:
        return ""
    parts = [f"\n# Casos de ejemplo ({len(visible)} visibles; el validador usa además {len(cases) - len(visible)} ocultos)"]
    for c in visible:
        parts.append(f"\n## {c.name}\nEntrada (formato de la instancia):\n```\n{c.text.strip()}\n```")
        for s in c.solutions:
            extra = f", costo {s['cost']:g}" if s.get("cost") is not None else ""
            extra += f", viola {s['violates']}" if s.get("violates") else ""
            parts.append(f"- respuesta `{json.dumps(s['answer'])}`: {'factible' if s['feasible'] else 'INFACTIBLE'}{extra}")
    return "\n".join(parts)


def model_prompt(spec, cases) -> str:
    instance = outline.py_outline(spec.instance_source) if outline.compact_default() else spec.instance_source
    return "\n".join([
        f"# Tarea\nEscribe en C++ el modelo del problema **{spec.name}**.",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia\nTu `Model::parse(text)` recibe la instancia en el formato que produce `to_text()` de esta clase "
        f"(Python, solo como especificación de los datos y del formato):\n```python\n{instance}\n```",
        f"\n# La solución\n`Solution` es `std::vector<std::vector<int>>` con la forma de la respuesta del problema: "
        f"{spec.answer_format}",
        f"\n# Familias de restricciones y términos del costo\n{spec.families}",
        f"\n# Contrato (native/include/hsf/generic.hpp)\n```cpp\n{contract_text()}\n```",
        _cases_block(cases),
        "\nDevuelve UN solo bloque ```cpp``` con `model.hpp` completo.",
    ])


def correction_prompt(source: str, feedback: str) -> str:
    return "\n".join([
        "Tu modelo C++ fue RECHAZADO. Corrígelo sin romper lo que ya funcionaba.",
        f"\n# Reporte\n{feedback}",
        f"\n# Tu modelo (las ediciones se aplican sobre él)\n```cpp\n{source}\n```",
        f"\n# Formato de la respuesta\n{EDIT_INSTRUCTIONS}",
    ])


def _compile_feedback(stderr: str) -> str:
    lines = [ln for ln in stderr.splitlines() if "model.hpp" in ln or "error" in ln][:40]
    return "No compila:\n" + "\n".join(lines or stderr.splitlines()[-40:])


def generate_native_model(client, pack, workspace: str | Path, rounds: int = 4, verbose: bool = True) -> dict:
    mip_parts = pack.variants[next(iter(pack.variants))][1] if pack.variants else f"{pack.module}.model_parts"
    ws = Path(workspace)
    model_dir = ws / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    gen = generation(model_dir, mip_parts)
    spec, cases = pack.make_model_spec(), pack.load_cases()
    stats = {"problem": pack.name, "compact_prompts": outline.compact_default(), "rounds": 0, "accepted": False,
             "rejections": [], "reply_modes": [],
             "model": getattr(client, "model", None)}
    tokens = TokenUsage()
    prompt, source = model_prompt(spec, cases), None
    t0 = time.perf_counter()
    for rnd in range(1, rounds + 1):
        stats["rounds"] = rnd
        text = client.complete(MODEL_SYSTEM_PROMPT, prompt)
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        try:
            if source is None:
                blocks = _BLOCK.findall(text)
                if not blocks:
                    raise EditError("la respuesta no trae un bloque ```cpp```")
                cand, mode = blocks[0].strip("\n") + "\n", "full"
            else:
                merged = merge_reply(source, text)
                cand, mode = merged.source, merged.mode
        except EditError as exc:
            stats["rejections"].append(f"respuesta inaplicable: {exc}")
            prompt = f"Tu respuesta no se pudo aplicar: {exc}.\n\n" + (correction_prompt(source, str(exc)) if source else model_prompt(spec, cases))
            continue
        stats["reply_modes"].append(mode)
        source = cand
        (model_dir / f"model_r{rnd}.hpp").write_text(source)
        (model_dir / "model.hpp").write_text(source)
        try:
            so, module = build_components(gen, [], debug=True)
            res = run_model_check({"problem": pack.name, "so": str(so), "module": module, "mip_parts": mip_parts,
                                   "out_dir": str(model_dir)})
        except NativeBuildError as exc:
            res = {"passed": False, "failed_layer": "compile", "feedback": _compile_feedback(str(exc))}
        if verbose:
            print(f"[modelo C++] ronda {rnd}: " + ("✔ " + res["feedback"] if res["passed"] else f"✘ {res['failed_layer']}"),
                  flush=True)
        if res["passed"]:
            stats.update(accepted=True, objective_rate=round(res.get("objective_rate", 0)))
            break
        stats["rejections"].append(f"[{res['failed_layer']}] {res['feedback'][-2500:]}")
        prompt = correction_prompt(source, res["feedback"])
    if not stats["accepted"]:
        (model_dir / "model.hpp").unlink(missing_ok=True)
    stats["wall_seconds"] = round(time.perf_counter() - t0, 1)
    stats["tokens"] = tokens.as_dict(getattr(client, "model", None))
    (ws / "model_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    return stats


def main(argv: list[str] | None = None) -> None:
    from .client import make_client
    from core.packs import base_pack

    ap = argparse.ArgumentParser(prog="python -m llm.native_model_generator")
    ap.add_argument("--problem", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--full-prompts", action="store_true",
                    help="código completo de lo que el LLM solo usa, en lugar de sus prototipos (llm/outline.py)")
    args = ap.parse_args(argv)
    if args.full_prompts:
        os.environ[outline.ENV] = "0"
    stats = generate_native_model(make_client(args.provider, args.model), base_pack(args.problem), args.workspace, args.rounds)
    print(json.dumps({k: v for k, v in stats.items() if k != "rejections"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

