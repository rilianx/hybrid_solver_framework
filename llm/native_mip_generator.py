"""La vista MIP del problema escrita por el LLM: variables, restricciones por familia, términos del objetivo y la
partición en grupos, como DATOS en Python (el framework arma el modelo para CBC). La usa HYB en sus sub-MIPs.

    python -m llm.native_mip_generator --problem clsp --workspace generated/clsp_native --provider anthropic

Lo humano del problema es el oráculo (las piezas de referencia: violaciones y costo de una solución) y los casos de
prueba; la vista MIP se valida contra ellos (`core.validation.model_parts`):

1. `check_mip_view`: en soluciones factibles, infactibles y al azar (de los casos y de instancias de tamaño
   realista), cada familia del MIP se viola exactamente cuando el oráculo la reporta, cada término del objetivo vale lo
   mismo que en el oráculo, la ida y vuelta solución → asignación → solución funciona y `variable_groups` es una
   partición útil.
2. `check_mip_optimum`: el óptimo del MIP completo coincide con el óptimo de cada caso.

Queda en `<workspace>/mip/mip.py`; `tuning.cli` lo usa en lugar de la vista de referencia (`--mip`).
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import os
import re
import time
from pathlib import Path

from core.model_parts import HEURISTIC_PARTS, MIP_PARTS
from core.validation.base import ValidationReport, describe_exception, fail
from native.edits import EditError, apply_edits, find_edits

from . import outline
from .client import TokenUsage

_PY = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)

MIP_SYSTEM_PROMPT = """Eres un experto en programación entera que escribe la formulación MIP de un problema de optimización
combinatoria para un framework de solvers híbridos. La formulación la usan matheurísticas que fijan parte de la
solución y reoptimizan el resto con un solver MIP (CBC), así que debe ser CORRECTA (mismo óptimo que el problema) y
conviene que sea FUERTE (buena relajación lineal) y no más grande de lo necesario.

Reglas:
1. Un solo bloque ```python``` con el módulo completo: las funciones del contrato a nivel de módulo, con sus imports.
2. Solo describes el modelo como DATOS (variables, coeficientes, sentidos, lados derechos): no llames a ningún solver
   para armarlo. Para `aux_values` puedes calcular lo que haga falta (incluso resolver un LP chico con PuLP).
3. Puedes importar las funciones del oráculo que se indican (son de lectura: no las redefinas). Nada de otros módulos
   del problema.
4. Sin I/O ni estado global mutable."""

MIP_CONTRACT = '''
# Funciones a escribir (a nivel de módulo; `inst` es la instancia y `sol` una solución en la forma del oráculo)

def variables(inst) -> dict[str, tuple[float, float, str]]: ...   # {nombre: (cota_inf, cota_sup, "binary" | "continuous")}
def structural_variables(inst) -> list[str]: ...    # las variables de decisión que describen la solución (las demás son auxiliares)
def to_assignment(inst, sol) -> dict[str, float]: ...   # valor de TODAS las estructurales para `sol`
def aux_values(inst, sol) -> dict[str, float]: ...      # valor de TODAS las auxiliares en el punto de `sol` (p.ej. cargas, inventarios, tiempos)
def from_assignment(inst, x) -> "sol": ...          # inversa: from_assignment(inst, to_assignment(inst, sol)) == sol (factibles), en forma canónica
def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]: ...
    # {familia: [(coeficientes {variable: coef}, sentido "<=" | ">=" | "==", lado derecho), ...]}
    # El nombre de la familia (o su prefijo antes de un punto, p.ej. "visita.entrada") es el que usa el oráculo en
    # `violations`: se verificará que la familia del MIP se viola exactamente cuando el oráculo la reporta.
def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]: ...
    # {término: (coeficientes, constante)} con los MISMOS nombres de término que `cost_terms` del oráculo
def variable_groups(inst) -> dict[str, list[str]]: ...   # partición de structural_variables en bloques CHICOS
    # (al menos 4, ninguno con más de un tercio), según la estructura del problema: los sub-MIPs liberan grupos de
    # variables que interactúan (elementos cercanos, el mismo período, la misma máquina...)
'''


# ------------------------------------------------------------------ el oráculo que ve el LLM
def oracle_names(oracle) -> list[str]:
    """Las funciones del oráculo (la vista heurística: forma de la solución, violaciones y costo) y las auxiliares del
    módulo que usan, sin la vista MIP de referencia ni lo que solo ella usa."""
    defined = {n for n, f in vars(oracle).items()
               if inspect.isfunction(inspect.unwrap(f)) and getattr(f, "__module__", None) == oracle.__name__}
    todo = [n for n in HEURISTIC_PARTS if n in defined]
    seen: list[str] = []
    while todo:
        n = todo.pop(0)
        if n in seen or n in MIP_PARTS:
            continue
        seen.append(n)
        try:
            tree = ast.parse(inspect.getsource(inspect.unwrap(getattr(oracle, n))).strip())
        except (OSError, TypeError, SyntaxError):
            continue
        todo += [x.id for x in ast.walk(tree) if isinstance(x, ast.Name) and x.id in defined and x.id not in seen]
    return seen


def oracle_source(oracle, names: list[str]) -> str:
    order = {n: inspect.getsourcelines(inspect.unwrap(getattr(oracle, n)))[1] for n in names}
    return "\n\n".join(inspect.getsource(getattr(oracle, n)) for n in sorted(names, key=order.get))


def _cases_block(cases) -> str:
    visible = [c for c in cases if c.visible]
    parts = [f"\n# Casos de ejemplo ({len(visible)} visibles; el validador usa además {len(cases) - len(visible)} ocultos)"]
    for c in visible:
        parts.append(f"\n## {c.name}\nEntrada (formato de la instancia):\n```\n{c.text.strip()}\n```")
        for s in c.solutions:
            extra = f", costo {s['cost']:g}" if s.get("cost") is not None else ""
            extra += f", viola {s['violates']}" if s.get("violates") else ""
            parts.append(f"- respuesta `{json.dumps(s['answer'])}`: {'factible' if s['feasible'] else 'INFACTIBLE'}{extra}")
        if c.optimum is not None:
            parts.append(f"- costo óptimo de la instancia: {c.optimum:g}")
    return "\n".join(parts)


def mip_prompt(spec, cases, oracle, names: list[str]) -> str:
    return "\n".join([
        f"# Tarea\nEscribe la vista MIP del problema **{spec.name}**, como datos (ver el contrato).",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia (`{spec.instance_import}`)\n```python\n"
        f"{outline.py_outline(spec.instance_source) if outline.compact_default() else spec.instance_source}\n```",
        f"\n# Familias de restricciones y términos del costo\n{spec.families}",
        f"\n# El oráculo (`{oracle.__name__}`)\nDefine qué es una solución, qué viola y cuánto cuesta; tu formulación tiene "
        f"que coincidir con él. Puedes importar estas funciones con `from {oracle.__name__} import ...`: "
        f"{', '.join(f'`{n}`' for n in names)}.\n```python\n{oracle_source(oracle, names)}\n```",
        MIP_CONTRACT,
        _cases_block(cases),
        "\n# Lo que se verificará\n- En soluciones factibles, infactibles y al azar (de los casos y de instancias de tamaño "
        "realista): cada familia del MIP, evaluada en to_assignment ∪ aux_values, se viola exactamente cuando el oráculo "
        "reporta esa familia; cada término del objetivo vale lo mismo que en cost_terms.\n- La ida y vuelta "
        "from_assignment(to_assignment(sol)) devuelve sol en las factibles.\n- variable_groups es una partición de las "
        "estructurales en bloques chicos.\n- El óptimo del MIP completo coincide con el óptimo de cada caso.",
        "\nDevuelve UN solo bloque ```python``` con el módulo completo.",
    ])


def correction_prompt(source: str, feedback: str) -> str:
    return "\n".join([
        "La vista MIP fue RECHAZADA por el validador. Corrígela. El reporte dice qué pieza falla y con qué caso o "
        "solución; los casos ocultos se describen sin la instancia: corrige la formulación, no la ajustes a un caso.",
        f"\n# Reporte del validador\n{feedback}",
        f"\n# Vista MIP rechazada (las ediciones se aplican sobre ella)\n```python\n{source}\n```",
        "\n# Formato de la respuesta\nDevuelve SOLO los cambios, como bloques de edición sobre el módulo actual:\n\n"
        "<<<<<<< BUSCAR\n(texto exacto del módulo actual, que aparezca UNA sola vez)\n=======\n(el texto que lo reemplaza)\n"
        ">>>>>>> REEMPLAZAR\n\nPuedes usar varios bloques. Solo si conviene reescribir casi todo, devuelve el módulo "
        "completo en un bloque ```python```.",
    ])


# ------------------------------------------------------------------ validación
def forbidden_imports(source: str, oracle_name: str, allowed: list[str], forbidden_modules: list[str]) -> list[str]:
    """Imports que no se permiten: del oráculo, algo que no sea una de sus funciones permitidas (p.ej. la vista MIP de
    referencia) o el módulo entero; y los demás módulos prohibidos del problema."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == oracle_name:
                bad += [f"{node.module}.{a.name}" for a in node.names if a.name not in allowed]
            elif any(node.module == f or node.module.startswith(f + ".") for f in forbidden_modules):
                bad.append(node.module)
        elif isinstance(node, ast.Import):
            bad += [a.name for a in node.names if a.name == oracle_name
                    or any(a.name == f or a.name.startswith(f + ".") for f in forbidden_modules)]
    return sorted(set(bad))


def validate_mip(oracle, mip_file: Path, cases, scale_instances, time_limit: float = 20.0) -> ValidationReport:
    from core.packs import load_mip, with_mip
    from core.validation.model_parts import check_mip_optimum, check_mip_view

    report = ValidationReport(subject="vista MIP")
    try:
        parts = with_mip(oracle, load_mip(mip_file))
        missing = [n for n in MIP_PARTS if not hasattr(parts, n)]
        if missing:
            report.add(fail("syntactic", "contract", f"faltan las funciones {missing}"))
            return report
        for check in (lambda: check_mip_view(parts, cases, scale_instances=scale_instances),
                      lambda: check_mip_optimum(parts, cases, time_limit)):
            r = check()
            report.extend(r.results)
            if not r.passed:
                break
    except Exception as exc:  # noqa: BLE001  una excepción del código generado es un rechazo
        report.add(fail("semantic_mip", "runs", f"el módulo lanzó {describe_exception(exc)} durante la validación"))
    return report


# ------------------------------------------------------------------ el ciclo
def generate_mip(client, pack, workspace: str | Path, rounds: int = 4, time_limit: float = 20.0,
                 verbose: bool = True) -> dict:
    from core.packs import oracle_module

    ws = Path(workspace)
    mip_dir = ws / "mip"
    mip_dir.mkdir(parents=True, exist_ok=True)
    spec, cases, oracle = pack.make_model_spec(), pack.load_cases(), oracle_module(pack)
    names = oracle_names(oracle)
    forbidden = [m for m in spec.forbidden_modules if m != oracle.__name__]
    scale = pack.make_instances(2, 900, pack.parse_size(pack.default_size))
    stats = {"problem": pack.name, "compact_prompts": outline.compact_default(), "rounds": 0, "accepted": False,
             "rejections": [], "reply_modes": [],
             "model": getattr(client, "model", None)}
    tokens = TokenUsage()
    prompt, source = mip_prompt(spec, cases, oracle, names), None
    t0 = time.perf_counter()
    for rnd in range(1, rounds + 1):
        stats["rounds"] = rnd
        text = client.complete(MIP_SYSTEM_PROMPT, prompt)
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        try:
            edits = find_edits(text) if source is not None else []
            if edits:
                cand, mode = apply_edits(source, edits), "edits"
            else:
                blocks = _PY.findall(text)
                if not blocks:
                    raise EditError("la respuesta no trae un bloque ```python``` ni bloques de edición")
                cand, mode = blocks[0].strip("\n") + "\n", "full"
        except EditError as exc:
            stats["rejections"].append(f"respuesta inaplicable: {exc}")
            prompt = f"Tu respuesta no se pudo aplicar: {exc}.\n\n" + (
                correction_prompt(source, str(exc)) if source else mip_prompt(spec, cases, oracle, names))
            continue
        stats["reply_modes"].append(mode)
        source = cand
        path = mip_dir / f"mip_r{rnd}.py"
        path.write_text(source)
        bad = forbidden_imports(source, oracle.__name__, names, forbidden)
        if bad:
            report = ValidationReport(subject="vista MIP")
            report.add(fail("syntactic", "no_forbidden_imports",
                            f"el módulo importa {bad}: del oráculo solo puedes importar {names}"))
        else:
            report = validate_mip(oracle, path, cases, scale, time_limit)
        if verbose:
            print(f"[vista MIP] ronda {rnd}: " + ("✔" if report.passed else f"✘ {report.failed_layer}"), flush=True)
        if report.passed:
            (mip_dir / "mip.py").write_text(source)
            stats["accepted"] = True
            break
        stats["rejections"].append(f"[{report.failed_layer}] {report.feedback()[-2500:]}")
        prompt = correction_prompt(source, report.feedback())
    stats["wall_seconds"] = round(time.perf_counter() - t0, 1)
    stats["tokens"] = tokens.as_dict(getattr(client, "model", None))
    (ws / "mip_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    return stats


def main(argv: list[str] | None = None) -> None:
    from core.packs import base_pack

    from .client import make_client

    ap = argparse.ArgumentParser(prog="python -m llm.native_mip_generator")
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
    stats = generate_mip(make_client(args.provider, args.model), base_pack(args.problem), args.workspace, args.rounds)
    print(json.dumps({k: v for k, v in stats.items() if k != "rejections"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
