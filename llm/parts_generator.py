"""Generación del `ProblemModel` por piezas con un LLM, validada con casos de prueba.

Hasta tres etapas, cada una con su ciclo de corrección y validada contra lo ya aceptado:

1. **Vista heurística** (`core.model_parts.HEURISTIC_PARTS`): el LLM ve la descripción, la
   instancia, el formato de respuesta y los casos VISIBLES; escribe la representación,
   `from_answer`, `violations` y `cost_terms`. Se valida contra todos los casos, visibles y
   ocultos (`check_heuristic_view`).
2. **Vista MIP** (`MIP_PARTS`): con la etapa 1 congelada y a la vista, escribe variables,
   puente, familias de restricciones y términos del objetivo, como datos. Se valida punto a
   punto contra la etapa 1 (`check_mip_view`) y después con el solver contra los óptimos
   esperados (`check_mip_optimum`).

3. **Vista constructiva** (`CONSTRUCTION_PARTS`, si `spec.construction`): con las etapas
   anteriores congeladas, escribe `construction_view(inst)`: estado parcial, acciones, aplicar,
   completo y respaldo. Se valida recorriendo los casos con elecciones al azar: termina, no
   modifica el parcial y llega a soluciones factibles según la vista heurística
   (`check_construction_view`). Es lo que usan el greedy y la beam search del framework, así
   que con ella un problema nuevo entra al lado constructivo sin código escrito a mano.

La vista MIP se omite con `spec.mip = False`: el problema queda solo con el lado constructivo.
El módulo final es la concatenación de las etapas aceptadas.
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
# Función a escribir: la vista constructiva (la usan el constructor greedy y la beam search del framework)

def construction_view(inst): ...   # devuelve un objeto con estos métodos:
    # empty() -> parcial                    el estado inicial de una construcción
    # candidates(p) -> list[acción]         acciones posibles desde p; [] si p está completo o es un callejón sin salida
    # apply(p, a) -> parcial                un parcial NUEVO; p no se modifica (se verificará)
    # is_complete(p) -> bool                p ya describe una solución completa
    # to_solution(p) -> sol                 la solución de un parcial completo, en forma CANÓNICA y FACTIBLE
    # complete(p, rng) -> sol               respaldo: una solución factible desde un parcial sin candidatos
    # opcionales: lower_bound(p) -> float (cota inferior del costo de cualquier solución que complete p; poda la
    #             beam search) y key(p) -> hashable (dos parciales equivalentes dan la misma clave)
# El framework elige la acción en cada paso con un puntaje `score(p, a)` (menor es mejor) que se escribe después,
# así que el parcial y las acciones deben exponer atributos y métodos de consulta que un puntaje pueda leer.
# La vista es NEUTRAL: ofrece todas las acciones razonables, no decide cuál conviene (eso es del puntaje).
# Garantiza que toda construcción termina: si un puntaje puede hacer que se repita un estado o que la
# construcción se alargue sin fin, evítalo en `candidates` (p.ej. no volver a un estado ya recorrido, o un
# tope de pasos) y cierra con `complete`.
'''


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


def heuristic_prompt(spec: ModelSpec, cases: list[TestCase]) -> str:
    return "\n".join([
        f"# Tarea\nEscribe la vista heurística del modelo del problema **{spec.name}**: la representación de una solución "
        "que manipularán las heurísticas, sus restricciones y su costo. La vista MIP se escribirá después.",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia (importa con `from {spec.instance_import} import ...`)\n```python\n{spec.instance_source}\n```",
        f"\n# Formato neutral de respuesta (el de los casos)\n{spec.answer_format}",
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
        MIP_CONTRACT,
        _cases_block(spec, cases, with_optimum=True),
        "\n# Lo que se verificará\n- En soluciones factibles, infactibles y al azar: cada familia del MIP se evalúa en "
        "to_assignment ∪ aux_values y debe violarse exactamente cuando violations reporta esa familia; cada término del "
        "objetivo debe valer lo mismo que en cost_terms.\n- El óptimo del MIP completo debe coincidir con el óptimo esperado "
        "de cada caso.",
        "\nDevuelve UN solo bloque ```python``` solo con las funciones de la vista MIP (y sus imports).",
    ])


def construction_prompt(spec: ModelSpec, cases: list[TestCase], approved_source: str) -> str:
    return "\n".join([
        f"# Tarea\nEscribe la vista constructiva del modelo del problema **{spec.name}**. El modelo ya está escrito y "
        "aprobado contra los casos de prueba: NO lo cambies ni lo redefinas; tu código se concatena DESPUÉS de él, así que "
        "puedes usar sus funciones (canonical, violations, cost_terms, trivial_solution…) directamente; no lo importes.",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia\n```python\n{spec.instance_source}\n```",
        f"\n# Modelo aprobado (ya definido antes de tu código)\n```python\n{approved_source}\n```",
        CONSTRUCTION_CONTRACT,
        *([f"\n# Sobre las acciones de este problema\n{spec.construction_notes}"] if spec.construction_notes else []),
        _cases_block(spec, cases),
        "\n# Lo que se verificará\n- En cada caso, recorridos con la primera acción y con acciones al azar: la construcción "
        "termina, apply no modifica el parcial y la solución (to_solution o complete) es canónica y FACTIBLE según "
        "violations.\n- Si defines lower_bound: nunca supera el costo de la solución a la que se llega ni el óptimo del caso.",
        "\nDevuelve UN solo bloque ```python``` solo con la vista constructiva (y sus imports).",
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


def _concat(heuristic: str, *later: tuple[str, str] | str) -> str:
    """Las etapas en un módulo: la heurística y después cada `(título, código)` (un `str` suelto
    es la vista MIP). Los `from __future__ import` tienen que ir al principio del archivo: se
    suben (el LLM los pone en todas las etapas)."""
    stages = [("", heuristic)] + [("vista MIP", x) if isinstance(x, str) else x for x in later]
    future, bodies = [], []
    for title, src in stages:
        lines = src.splitlines()
        future += [ln for ln in lines if ln.startswith("from __future__ import")]
        body = "\n".join(ln for ln in lines if not ln.startswith("from __future__ import")).strip("\n")
        bodies.append(body if not title else f"# ---- {title} ----\n{body}")
    head = "\n".join(dict.fromkeys(future))
    return (head + "\n\n" if head else "") + "\n\n\n".join(bodies) + "\n"


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


def _run_checks(checks, subject: str = "vista MIP") -> ValidationReport:
    """Los validadores en orden; una excepción del código generado es un rechazo, no una caída."""
    report = ValidationReport(subject=subject)
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
                                 scale_instances: list | None = None) -> PartsGenerationResult:
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
    context1 = f"\n# El problema\n{spec.description}\n\n# Formato de respuesta\n{spec.answer_format}\n{HEURISTIC_CONTRACT}"
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
            report = check_heuristic_view(module, cases)
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

    # etapa 2: vista MIP, concatenada después de la heurística (opcional)
    approved, later = res.heuristic.source, []
    if spec.mip:
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
                report = _run_checks([lambda: check_mip_view(module, cases, scale_instances=scale_instances),
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
        if not res.mip.accepted:
            res.seconds = time.perf_counter() - t0
            return res
        later.append(("vista MIP", res.mip.source))
        approved = _concat(res.heuristic.source, *later)
    else:
        path = ws / "model_heuristic.py"
        path.write_text(_concat(res.heuristic.source))
        res.path = path

    # etapa 3: vista constructiva, concatenada al final (opcional)
    if spec.construction:
        res.path = None
        context3 = (f"\n# El problema\n{spec.description}\n\n# Modelo aprobado (no lo cambies)\n```python\n"
                    f"{approved}\n```\n{CONSTRUCTION_CONTRACT}")
        prompt = construction_prompt(spec, cases, approved)
        for rnd in range(1, max_rounds + 1):
            res.construction.rounds = rnd
            src = ask(prompt)
            if src is None:
                res.construction.reports.append("sin bloque ```python```")
                continue
            path = ws / f"model_constructive_r{rnd}.py"
            path.write_text(_concat(res.heuristic.source, *later, ("vista constructiva", src)))
            clash = redefined_names(approved, src)
            if clash:
                module, report = None, ValidationReport(subject=path.name)
                report.add(fail("syntactic", "no_redefinition",
                                f"la vista constructiva vuelve a definir {clash}, que ya están en el modelo aprobado: úsalos tal "
                                f"cual y ponle otro nombre a tus funciones auxiliares"))
            else:
                module, report = _load(path, spec.forbidden_modules)
            if module is not None:
                report = _run_checks([lambda: check_construction_view(module, cases)], subject="vista constructiva")
            if report.passed:
                res.construction.accepted, res.construction.source, res.path = True, src, path
                if verbose:
                    print(f"[modelo/constructiva] ✔ ronda {rnd}")
                break
            res.construction.reports.append(report.feedback())
            if verbose:
                print(f"[modelo/constructiva] ✘ ronda {rnd}: {report.failed_layer}")
            prompt = correction_prompt("vista constructiva", src, report.feedback(), context3)
    res.seconds = time.perf_counter() - t0
    return res


__all__ = ["PartsGenerationResult", "construction_prompt", "generate_problem_model_parts", "heuristic_prompt", "mip_prompt",
           "redefined_names"]
