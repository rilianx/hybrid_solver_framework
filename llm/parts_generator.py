"""Generación del `ProblemModel` por piezas con un LLM, validada con casos de prueba.

Dos etapas, cada una con su ciclo de corrección y validada contra lo ya aceptado:

1. **Vista heurística** (`core.model_parts.HEURISTIC_PARTS`): el LLM ve la descripción, la
   instancia, el formato de respuesta y los casos VISIBLES; escribe la representación,
   `from_answer`, `violations` y `cost_terms`. Se valida contra todos los casos, visibles y
   ocultos (`check_heuristic_view`).
2. **Vista MIP** (`MIP_PARTS`): con la etapa 1 congelada y a la vista, escribe variables,
   puente, familias de restricciones y términos del objetivo, como datos. Se valida punto a
   punto contra la etapa 1 (`check_mip_view`) y después con el solver contra los óptimos
   esperados (`check_mip_optimum`).

El módulo final es la concatenación de las dos etapas.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.model_parts import TestCase
from core.validation.base import ValidationReport, fail
from core.validation.model_parts import check_construction_view, check_heuristic_view, check_mip_optimum, check_mip_view
from core.validation.syntactic import load_module

from .client import LLMClient, TokenUsage
from .model_generator import ModelSpec, _imports
from .parser import extract_code_blocks
from .prompts import MODEL_SYSTEM_PROMPT

HEURISTIC_CONTRACT = '''
# Funciones a escribir (a nivel de módulo; `inst` es la instancia)

def canonical(sol): ...                  # forma canónica de una solución (hashable, comparable con ==); idempotente
def trivial_solution(inst): ...          # una solución FACTIBLE cualquiera, en forma canónica
def random_solution(inst, rng): ...      # una solución al azar con estructura válida (rng = random.Random), canónica
def from_answer(inst, answer): ...       # la respuesta en el FORMATO NEUTRAL de los casos -> tu representación, canónica
def violations(inst, sol) -> dict[str, float]: ...   # {familia: magnitud}; > 0 = violada; usa los nombres de familia indicados
def cost_terms(inst, sol) -> dict[str, float]: ...   # el objetivo (a MINIMIZAR) desglosado por términos
'''

MIP_CONTRACT = '''
# Funciones a escribir: la vista MIP como DATOS (el framework arma el modelo del solver y lo resuelve)

def variables(inst) -> dict[str, tuple[float, float, str]]: ...   # {nombre: (cota_inf, cota_sup, "binary" | "continuous")}
def structural_variables(inst) -> list[str]: ...    # las binarias que describen la solución (las demás son auxiliares)
def to_assignment(inst, sol) -> dict[str, float]: ...   # valor de TODAS las estructurales para `sol`
def aux_values(inst, sol) -> dict[str, float]: ...      # valor de TODAS las auxiliares en el punto de `sol` (p.ej. cargas, inventarios)
def from_assignment(inst, x) -> "sol": ...          # inversa: from_assignment(inst, to_assignment(inst, sol)) == sol (factibles)
def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]: ...
    # {familia: [(coeficientes {variable: coef}, sentido "<=" | ">=" | "==", lado derecho), ...]}
    # El nombre de la familia (o su prefijo antes de un punto, p.ej. "visita.entrada") debe ser el nombre que
    # usa `violations`: se verificará que la familia del MIP se viola exactamente cuando violations la reporta.
def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]: ...
    # {término: (coeficientes, constante)} con los MISMOS nombres de término que cost_terms
def variable_groups(inst) -> dict[str, list[str]]: ...   # partición de structural_variables en bloques CHICOS
    # (al menos 4, ninguno con más de un tercio), según la estructura del problema: Fix-and-Optimize
    # libera de a 1 a 4 grupos por subproblema, y Relax-and-Fix fija un grupo por vez. Agrupa variables que
    # interactúan (elementos cercanos, el mismo período…): con todo lo demás fijo, liberar un grupo tiene que
    # dejar espacio para cambiar la solución
'''


CONSTRUCTION_CONTRACT = '''
# Funciones a escribir: la vista constructiva (para un constructor greedy genérico del framework)

def empty_partial(inst): ...                        # la solución parcial vacía (un objeto tuyo: tupla, dataclass...)
def candidates(inst, partial) -> list: ...           # acciones válidas desde `partial` (lista; vacía si no queda ninguna)
def apply_action(inst, partial, action): ...        # parcial NUEVA con la acción aplicada; NO modifiques `partial`
def is_complete(inst, partial) -> bool: ...
def to_solution(inst, partial): ...                 # la solución (en la representación de la vista heurística, canónica)
def complete_partial(inst, partial, rng): ...       # callejón sin salida (candidates vacío sin estar completa): termina
                                                    # como puedas, con una solución FACTIBLE (rng = random.Random)

# El framework construye así (el puntaje que elige entre candidatos lo escribirá después otro modelo):
#     partial = empty_partial(inst)
#     while not is_complete(inst, partial):
#         C = candidates(inst, partial)
#         if not C: return complete_partial(inst, partial, rng)
#         partial = apply_action(inst, partial, elegido_por_el_puntaje(C))
#     return to_solution(inst, partial)
# Regla de oro: elegir CUALQUIER candidato en cada paso tiene que llevar a una solución factible. La calidad la pone
# el puntaje; la factibilidad, tus candidatos. Las acciones deben llevar la información que un puntaje necesita para
# comparar (p.ej. el aumento de costo que producen), porque el puntaje solo ve (partial, acción).
'''


def construction_prompt(spec: ModelSpec, cases: list[TestCase], heuristic_source: str) -> str:
    return "\n".join([
        f"# Tarea\nEscribe la vista constructiva del modelo del problema **{spec.name}**: cómo se arma una solución paso a "
        "paso. La vista heurística ya está escrita y aprobada: NO la cambies ni la redefinas; tu módulo se concatena "
        "DESPUÉS de ella, así que puedes usar sus funciones (canonical, violations, cost_terms…) directamente; no la importes.",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia\n```python\n{spec.instance_source}\n```",
        f"\n# Vista heurística aprobada (ya definida antes de tu código)\n```python\n{heuristic_source}\n```",
        CONSTRUCTION_CONTRACT,
        *([f"\n# Sobre la construcción en este problema\n{spec.construction}"] if spec.construction else []),
        _cases_block(spec, cases),
        "\n# Lo que se verificará\n- En cada caso y en instancias de tamaño realista: varias construcciones eligiendo "
        "candidatos AL AZAR terminan, sin modificar las parciales, y dan soluciones canónicas y factibles según violations.\n"
        "- Las construcciones al azar dan soluciones distintas (los candidatos ofrecen decisiones reales).\n"
        "- Una construcción en una instancia de tamaño realista tarda pocos segundos.",
        "\nDevuelve UN solo bloque ```python``` solo con las funciones de la vista constructiva (y sus imports).",
    ])


def _cases_block(spec: ModelSpec, cases: list[TestCase], with_optimum: bool = False) -> str:
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
        if with_optimum and c.optimum is not None:
            parts.append(f"- costo óptimo de la instancia: {c.optimum:g}")
    return "\n".join(parts)


def _representation_block(spec: ModelSpec) -> str:
    if not spec.representation:
        return "\n# Representación de la solución\nElígela tú: hashable y comparable con ==."
    text = f"\n# Representación de la solución (obligatoria)\n{spec.representation}"
    if spec.decoder:
        text += ("\nEs una codificación: from_answer debe devolver una codificación cuya decodificación sea la respuesta del "
                 "caso o una igual de buena o mejor; se verificará que el costo no sea peor que el esperado.")
    return text


def heuristic_prompt(spec: ModelSpec, cases: list[TestCase]) -> str:
    return "\n".join([
        f"# Tarea\nEscribe la vista heurística del modelo del problema **{spec.name}**: la representación de una solución "
        "que manipularán las heurísticas, sus restricciones y su costo. La vista MIP se escribirá después.",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia (importa con `from {spec.instance_import} import ...`)\n```python\n{spec.instance_source}\n```",
        f"\n# Formato neutral de respuesta (el de los casos)\n{spec.answer_format}",
        _representation_block(spec),
        f"\n# Familias de restricciones y términos del objetivo\n{spec.families}",
        HEURISTIC_CONTRACT,
        _cases_block(spec, cases),
        *([f"\n# Avisos\n" + "\n".join(f"- {n}" for n in spec.notes)] if spec.notes else []),
        "\nDevuelve UN solo bloque ```python``` con el módulo completo (imports incluidos).",
    ])


def mip_prompt(spec: ModelSpec, cases: list[TestCase], heuristic_source: str) -> str:
    return "\n".join([
        f"# Tarea\nEscribe la vista MIP del modelo del problema **{spec.name}**, como DATOS (sin llamar a ningún solver). "
        "La vista heurística ya está escrita y aprobada contra los casos de prueba: NO la cambies ni la redefinas; tu "
        "módulo se concatena DESPUÉS de ella, así que puedes usar sus funciones (canonical, cost_terms…) directamente; "
        "no la importes (no es un módulo aparte).",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia\n```python\n{spec.instance_source}\n```",
        f"\n# Vista heurística aprobada (ya definida antes de tu código)\n```python\n{heuristic_source}\n```",
        _representation_block(spec),
        *(["La representación es una codificación: la ida y vuelta from_assignment(to_assignment(sol)) NO tiene que "
           "devolver la misma codificación; se exige que sea factible y no peor que sol. to_assignment y aux_values describen "
           "la solución DECODIFICADA."] if spec.decoder else []),
        MIP_CONTRACT,
        _cases_block(spec, cases, with_optimum=True),
        "\n# Lo que se verificará\n- En soluciones factibles, infactibles y al azar: cada familia del MIP se evalúa en "
        "to_assignment ∪ aux_values y debe violarse exactamente cuando violations reporta esa familia; cada término del "
        "objetivo debe valer lo mismo que en cost_terms.\n- El óptimo del MIP completo debe coincidir con el óptimo esperado "
        "de cada caso.",
        "\nDevuelve UN solo bloque ```python``` solo con las funciones de la vista MIP (y sus imports).",
    ])


def correction_prompt(stage: str, source: str, feedback: str, context: str) -> str:
    return "\n".join([
        f"La {stage} fue RECHAZADA por el validador. Corrígela y devuelve el código completo de esa etapa en un único bloque "
        "```python```. El reporte dice qué pieza falla y con qué caso o solución; los casos ocultos se describen sin la "
        "instancia: corrige el modelo, no lo ajustes a un caso.",
        f"\n# Reporte del validador\n{feedback}",
        context,
        f"\n# Código rechazado\n```python\n{source}\n```",
    ])


@dataclass
class StageResult:
    accepted: bool = False
    rounds: int = 0
    reports: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class PartsGenerationResult:
    path: Path | None
    heuristic: StageResult
    mip: StageResult
    construction: StageResult = field(default_factory=StageResult)
    llm_calls: int = 0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    seconds: float = 0.0


def _concat(heuristic: str, mip: str, construction: str | None = None) -> str:
    """Las etapas en un módulo. Los `from __future__ import` tienen que ir al principio del
    archivo: se suben (el LLM los pone en todas las etapas)."""
    future, bodies = [], []
    for src in (heuristic, mip, construction):
        if src is None:
            continue
        lines = src.splitlines()
        future += [ln for ln in lines if ln.startswith("from __future__ import")]
        bodies.append("\n".join(ln for ln in lines if not ln.startswith("from __future__ import")).strip("\n"))
    head = "\n".join(dict.fromkeys(future))
    out = (head + "\n\n" if head else "") + bodies[0] + "\n\n\n# ---- vista MIP ----\n" + bodies[1] + "\n"
    if len(bodies) > 2:
        out += "\n\n# ---- vista constructiva ----\n" + bodies[2] + "\n"
    return out


def _top_level_defs(src: str) -> dict[str, str]:
    """Nombre de nivel superior -> su definición normalizada (ast.dump)."""
    import ast

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    defs: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs[node.name] = ast.dump(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            defs.update({t.id: ast.dump(node) for t in targets if isinstance(t, ast.Name)})
    return defs


def redefined_names(heuristic: str, mip: str) -> list[str]:
    """Nombres de la vista heurística aprobada que la vista MIP vuelve a definir DISTINTO. Corrida
    25: la vista MIP redefinió `_min_cost_max_flow` con otro valor de retorno y rompió `violations`.
    Una copia idéntica (corrida 28: `canonical`) no cambia nada y se deja pasar."""
    h, m = _top_level_defs(heuristic), _top_level_defs(mip)
    return sorted(n for n in h.keys() & m.keys() if h[n] != m[n])


def _run_checks(checks) -> ValidationReport:
    """Los validadores en orden; una excepción del código generado es un rechazo, no una caída."""
    report = ValidationReport(subject="vista MIP")
    for check in checks:
        try:
            r = check()
        except Exception as exc:  # noqa: BLE001
            report.add(fail("semantic_mip", "runs", f"el módulo lanzó {type(exc).__name__}: {exc} durante la validación"))
            return report
        report.extend(r.results)
        if not r.passed:
            break
    return report


def _load(path: Path, forbidden: list[str]):
    bad = sorted(m for m in _imports(path.read_text()) if any(m == f or m.startswith(f + ".") for f in forbidden))
    if bad:
        r = ValidationReport(subject=path.name)
        r.add(fail("syntactic", "no_forbidden_imports", f"el módulo importa {bad}: escribe el modelo, no lo importes"))
        return None, r
    module, res = load_module(path)
    r = ValidationReport(subject=path.name)
    r.add(res)
    return module, r


def generate_problem_model_parts(client: LLMClient, spec: ModelSpec, cases: list[TestCase], workspace: str | Path,
                                 max_rounds: int = 4, mip_time_limit: float = 20.0, verbose: bool = True,
                                 scale_instances: list | None = None, construction: bool = True) -> PartsGenerationResult:
    """`scale_instances`: instancias de tamaño realista para medir la granularidad de `variable_groups`."""
    ws = Path(workspace) / "problem_model"
    ws.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    res = PartsGenerationResult(path=None, heuristic=StageResult(), mip=StageResult())

    def ask(prompt: str) -> str | None:
        text = client.complete(MODEL_SYSTEM_PROMPT, prompt)
        res.llm_calls += 1
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            res.tokens.add(used)
        blocks = extract_code_blocks(text)
        return blocks[0] if blocks else None

    # etapa 1: vista heurística
    context1 = (f"\n# El problema\n{spec.description}\n\n# Formato de respuesta\n{spec.answer_format}\n"
                f"{_representation_block(spec)}\n{HEURISTIC_CONTRACT}")
    prompt = heuristic_prompt(spec, cases)
    for rnd in range(1, max_rounds + 1):
        res.heuristic.rounds = rnd
        src = ask(prompt)
        if src is None:
            res.heuristic.reports.append("sin bloque ```python```")
            continue
        path = ws / f"heuristic_r{rnd}.py"
        path.write_text(src)
        module, report = _load(path, spec.forbidden_modules)
        if module is not None:
            report = check_heuristic_view(module, cases, decoder=spec.decoder)
        if report.passed:
            res.heuristic.accepted, res.heuristic.source = True, src
            if verbose:
                print(f"[modelo/heurística] ✔ ronda {rnd}")
            break
        res.heuristic.reports.append(report.feedback())
        if verbose:
            print(f"[modelo/heurística] ✘ ronda {rnd}: {report.failed_layer}")
        prompt = correction_prompt("vista heurística", src, report.feedback(), context1)
    if not res.heuristic.accepted:
        res.seconds = time.perf_counter() - t0
        return res

    # etapa 2: vista MIP, concatenada después de la heurística
    context2 = (f"\n# El problema\n{spec.description}\n\n# Vista heurística aprobada (no la cambies)\n```python\n"
                f"{res.heuristic.source}\n```\n{MIP_CONTRACT}")
    prompt = mip_prompt(spec, cases, res.heuristic.source)
    for rnd in range(1, max_rounds + 1):
        res.mip.rounds = rnd
        src = ask(prompt)
        if src is None:
            res.mip.reports.append("sin bloque ```python```")
            continue
        path = ws / f"model_r{rnd}.py"
        path.write_text(_concat(res.heuristic.source, src))
        clash = redefined_names(res.heuristic.source, src)
        if clash:
            module, report = None, ValidationReport(subject=path.name)
            report.add(fail("syntactic", "no_redefinition",
                            f"la vista MIP vuelve a definir {clash}, que ya están en la vista heurística aprobada (tu código se "
                            f"concatena después y los reemplaza): usa los de la vista heurística tal cual y ponle otro nombre "
                            f"a tus funciones auxiliares"))
        else:
            module, report = _load(path, spec.forbidden_modules)
        if module is not None:
            report = _run_checks([lambda: check_mip_view(module, cases, scale_instances=scale_instances, decoder=spec.decoder),
                                  lambda: check_mip_optimum(module, cases, mip_time_limit)])
        if report.passed:
            res.mip.accepted, res.mip.source, res.path = True, src, path
            if verbose:
                print(f"[modelo/MIP] ✔ ronda {rnd}")
            break
        res.mip.reports.append(report.feedback())
        if verbose:
            print(f"[modelo/MIP] ✘ ronda {rnd}: {report.failed_layer}")
        prompt = correction_prompt("vista MIP", src, report.feedback(), context2)
    if construction and res.mip.accepted:
        _construction_stage(res, spec, cases, ws, ask, max_rounds, scale_instances, verbose)
    res.seconds = time.perf_counter() - t0
    return res


def _construction_stage(res, spec, cases, ws, ask, max_rounds, scale_instances, verbose) -> None:
    """Etapa 3 (opcional): la vista constructiva, concatenada después de la heurística y la MIP. Si no
    se acepta, el modelo queda sin ella (el ciclo usa entonces constructores completos)."""
    context3 = (f"\n# El problema\n{spec.description}\n\n# Vista heurística aprobada (no la cambies)\n```python\n"
                f"{res.heuristic.source}\n```\n{CONSTRUCTION_CONTRACT}")
    prompt = construction_prompt(spec, cases, res.heuristic.source)
    for rnd in range(1, max_rounds + 1):
        res.construction.rounds = rnd
        src = ask(prompt)
        if src is None:
            res.construction.reports.append("sin bloque ```python```")
            continue
        path = ws / f"model_c{rnd}.py"
        path.write_text(_concat(res.heuristic.source, res.mip.source, src))
        clash = redefined_names(res.heuristic.source + "\n" + res.mip.source, src)
        if clash:
            module, report = None, ValidationReport(subject=path.name)
            report.add(fail("syntactic", "no_redefinition",
                            f"la vista constructiva vuelve a definir {clash}, que ya están en las vistas aprobadas (tu código se "
                            f"concatena después y los reemplaza): usa los de ellas tal cual y ponle otro nombre a tus auxiliares"))
        else:
            module, report = _load(path, spec.forbidden_modules)
        if module is not None:
            report = _run_checks([lambda: check_construction_view(module, cases, scale_instances=scale_instances)])
        if report.passed:
            res.construction.accepted, res.construction.source, res.path = True, src, path
            if verbose:
                print(f"[modelo/construcción] ✔ ronda {rnd}")
            return
        res.construction.reports.append(report.feedback())
        if verbose:
            print(f"[modelo/construcción] ✘ ronda {rnd}: {report.failed_layer}")
        prompt = correction_prompt("vista constructiva", src, report.feedback(), context3)


__all__ = ["PartsGenerationResult", "construction_prompt", "generate_problem_model_parts", "heuristic_prompt", "mip_prompt", "redefined_names"]
