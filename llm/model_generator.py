"""Generación del `ProblemModel` completo con un LLM (§6.1): el modelo, no solo los componentes.

El LLM recibe la descripción del problema y la clase de la instancia, y escribe un módulo con

    build_problem_model(inst) -> ProblemModel      # objective, is_feasible, build_mip, to/from_assignment, variable_groups
    trivial_solution(inst)    -> Solution          # una solución factible cualquiera

La validación es la capa semántica (`core.validation.semantic_mip`): cada vista valida a la
otra. En micro-instancias, la solución trivial tiene que ser factible para el modelo, fijarla
en el MIP tiene que dar el mismo objetivo que `objective`, el puente de ida y vuelta tiene que
conservarla y el MIP completo no puede ser peor que ella. Un desacuerdo no dice qué vista está
mal, pero sí que una lo está, y el reporte vuelve al LLM para corregir.

Si existe un modelo de referencia (en los ejemplos, el escrito a mano), `cross_check` compara
el óptimo del MIP generado con el del de referencia en las mismas micro-instancias. Es
independiente de la representación que elija el LLM y detecta lo que la capa semántica no
puede: dos vistas coherentes entre sí que modelan otro problema. Se reporta como evaluación;
no se usa para aceptar, porque en un problema nuevo no habrá referencia.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.validation import ValidationContext, ValidationReport
from core.validation.base import fail, guard, ok
from core.validation.semantic_mip import check_problem_model_mip
from core.validation.syntactic import load_module

from .client import LLMClient, TokenUsage
from .parser import extract_code_blocks
from .prompts import MODEL_SYSTEM_PROMPT

LAYER = "semantic_mip"

MODEL_CONTRACT = '''
# Contrato del módulo (lo que se importa y se valida)

def build_problem_model(inst) -> "ProblemModel":
    """El modelo ligado a la instancia. Debe exponer `inst` como atributo y estos métodos:"""

class ProblemModel:
    inst: Any
    def objective(self, sol) -> float: ...          # MINIMIZAR; finito también para soluciones infactibles (penalízalas)
    def is_feasible(self, sol) -> bool: ...
    def build_mip(self, inst) -> "MIPModel": ...
    def to_assignment(self, sol) -> dict[str, float]: ...   # valor de TODAS las variables de build_mip(inst).variables()
    def from_assignment(self, x: dict[str, float]): ...     # inversa: from_assignment(to_assignment(sol)) == sol
    def variable_groups(self, inst) -> dict[str, list[str]]: ...  # partición de las variables del MIP (p.ej. por período, por sector)

class MIPModel:                                     # con PuLP y el solver CBC (pulp.PULP_CBC_CMD(msg=False, timeLimit=...))
    last_objective: float | None                    # objetivo del último solve exitoso
    def variables(self) -> list[str]: ...           # las variables enteras/binarias (los nombres de to_assignment)
    def solve(self, fixed: dict[str, float], integer: set[str], relaxed: set[str], time_limit: float,
              warm_start: dict[str, float] | None = None, near: tuple[dict[str, float], int] | None = None
              ) -> dict[str, float] | None: ...
        # Toda variable de variables() cae en exactamente uno de: fixed (valor fijo), integer (binaria), relaxed
        # (continua en [0, 1]). near=(x̄, k): restricción de Local Branching, sum_{x̄_j=0} x_j + sum_{x̄_j=1} (1-x_j) <= k.
        # Devuelve la asignación de TODAS las variables de variables() (redondeadas las enteras) o None si no hay solución.

def trivial_solution(inst):
    """Una solución FACTIBLE cualquiera (se usa para validar el modelo)."""
'''


@dataclass
class ModelSpec:
    """Lo que se le da al LLM para escribir el modelo."""

    name: str
    description: str  # datos, restricciones y objetivo, en lenguaje natural
    instance_source: str  # código de la clase de instancia
    instance_import: str  # módulo desde donde se importa la clase de instancia
    notes: list[str] = field(default_factory=list)
    # módulos que el generado no puede importar (p.ej. el modelo de referencia: sería copiarlo)
    forbidden_modules: list[str] = field(default_factory=list)
    # generación por piezas (`llm.parts_generator`): formato neutral de las respuestas de los casos y
    # nombres de las familias de restricciones y de los términos del objetivo
    answer_format: str = ""
    families: str = ""


def model_prompt(spec: ModelSpec) -> str:
    notes = "\n".join(f"- {n}" for n in spec.notes)
    return "\n".join([
        f"# Tarea\nEscribe el módulo Python del modelo del problema **{spec.name}** para un framework de solvers "
        "híbridos: una vista estructural (la solución que manipulan las heurísticas) y una vista MIP (variables "
        "enteras para el solver), conectadas por to_assignment/from_assignment. Las dos vistas tienen que describir "
        "el MISMO problema: se verificará que coinciden.",
        f"\n# El problema\n{spec.description}",
        f"\n# La instancia (importa con `from {spec.instance_import} import ...`)\n```python\n{spec.instance_source}\n```",
        MODEL_CONTRACT,
        "\n# Lo que verificará el validador en micro-instancias\n"
        "- `trivial_solution(inst)` es factible según `is_feasible`.\n"
        "- `from_assignment(to_assignment(sol)) == sol` (elige una forma canónica de la solución si hace falta).\n"
        "- Fijar `to_assignment(sol)` en el MIP es factible, devuelve la misma solución y `last_objective == objective(sol)`.\n"
        "- El MIP completo (todas las variables enteras) no es peor que la solución trivial.\n"
        "- `variables()` del MIP y la unión de `variable_groups(inst)` son el mismo conjunto.",
        *([f"\n# Avisos\n{notes}"] if notes else []),
        "\nDevuelve UN solo bloque ```python``` con el módulo completo (imports incluidos).",
    ])


def model_correction_prompt(spec: ModelSpec, source: str, feedback: str) -> str:
    return "\n".join([
        f"El módulo del modelo de **{spec.name}** fue RECHAZADO por el validador semántico. Corrígelo y devuelve el "
        "módulo completo en un único bloque ```python```. Un desacuerdo entre las vistas indica que una de las dos está "
        "mal (la formulación MIP o la vista heurística): revisa ambas contra la descripción del problema.",
        f"\n# Reporte del validador\n{feedback}",
        f"\n# El problema\n{spec.description}",
        MODEL_CONTRACT,
        f"\n# Módulo rechazado\n```python\n{source}\n```",
    ])


def _imports(source: str) -> set[str]:
    import ast

    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def validate_model_module(path: str | Path, instances: list[Any], mip_time_limit: float = 10.0,
                          forbidden_modules: list[str] | None = None) -> tuple[ValidationReport, Any]:
    """Carga el módulo y corre la capa semántica en cada micro-instancia."""
    report = ValidationReport(subject=f"modelo '{Path(path).name}'")
    if forbidden_modules:
        try:
            bad = sorted(m for m in _imports(Path(path).read_text()) if any(m == f or m.startswith(f + ".") for f in forbidden_modules))
        except SyntaxError:
            bad = []
        if bad:
            report.add(fail("syntactic", "no_forbidden_imports",
                            f"el módulo importa {bad}: escribe el modelo, no lo importes (solo la instancia está permitida)"))
            return report, None
    module, r = load_module(path)
    report.add(r)
    if module is None:
        return report, None
    for fn in ("build_problem_model", "trivial_solution"):
        if not callable(getattr(module, fn, None)):
            report.add(fail("syntactic", f"defines_{fn}", f"el módulo no define `{fn}`"))
    if not report.passed:
        return report, module
    for k, inst in enumerate(instances):
        def _setup(inst=inst):
            P = module.build_problem_model(inst)
            sol = module.trivial_solution(inst)
            return P, sol

        try:
            P, sol = _setup()
        except Exception as exc:  # noqa: BLE001
            report.add(fail(LAYER, "build", f"build_problem_model/trivial_solution lanzó {type(exc).__name__} en inst_{k}: {exc}"))
            return report, module
        results = guard(LAYER, "trivial_feasible", lambda P=P, sol=sol, k=k: ok(LAYER, "trivial_feasible") if P.is_feasible(sol)
                        else fail(LAYER, "trivial_feasible", f"trivial_solution(inst_{k}) no es factible según is_feasible"))
        report.extend(results)
        if not report.passed:
            return report, module
        ctx = ValidationContext(problem=P, instances=[inst], trivial_solutions=[sol], mip_time_limit=mip_time_limit)
        report.extend(check_problem_model_mip(ctx))
        if not report.passed:
            return report, module
    return report, module


def cross_check(module, reference_factory: Callable[[Any], Any], instances: list[Any], time_limit: float = 20.0,
                tolerance: float = 1e-4) -> list[dict[str, Any]]:
    """Óptimo del MIP generado vs el del modelo de referencia, por micro-instancia."""
    rows = []
    for k, inst in enumerate(instances):
        row: dict[str, Any] = {"instance": k}
        for label, P in (("generated", module.build_problem_model(inst)), ("reference", reference_factory(inst))):
            model = P.build_mip(inst)
            x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=time_limit)
            row[label] = None if x is None else P.objective(P.from_assignment(x))
        g, r = row["generated"], row["reference"]
        row["match"] = g is not None and r is not None and abs(g - r) <= tolerance * max(1.0, abs(r))
        rows.append(row)
    return rows


@dataclass
class ModelGenerationResult:
    path: Path | None
    rounds: int
    llm_calls: int = 0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    reports: list[str] = field(default_factory=list)  # feedback de cada ronda rechazada
    seconds: float = 0.0


def generate_problem_model(client: LLMClient, spec: ModelSpec, instances: list[Any], workspace: str | Path,
                           max_rounds: int = 4, verbose: bool = True) -> ModelGenerationResult:
    workspace = Path(workspace) / "problem_model"
    workspace.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    res = ModelGenerationResult(path=None, rounds=0)
    prompt = model_prompt(spec)
    for round_no in range(1, max_rounds + 1):
        res.rounds = round_no
        text = client.complete(MODEL_SYSTEM_PROMPT, prompt)
        res.llm_calls += 1
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            res.tokens.add(used)
        blocks = extract_code_blocks(text)
        if not blocks:
            res.reports.append("la respuesta no trajo un bloque ```python```")
            prompt = model_prompt(spec)
            continue
        path = workspace / f"model_r{round_no}.py"
        path.write_text(blocks[0])
        report, _ = validate_model_module(path, instances, forbidden_modules=spec.forbidden_modules)
        if report.passed:
            res.path = path
            if verbose:
                print(f"[modelo] ✔ aceptado en la ronda {round_no}")
            break
        feedback = report.feedback()
        res.reports.append(feedback)
        if verbose:
            print(f"[modelo] ✘ ronda {round_no}: capa '{report.failed_layer}'")
        prompt = model_correction_prompt(spec, blocks[0], feedback)
    res.seconds = time.perf_counter() - t0
    return res


__all__ = ["ModelSpec", "cross_check", "generate_problem_model", "model_prompt", "validate_model_module"]
