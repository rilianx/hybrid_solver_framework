"""Tipos comunes de la validación autónoma por capas (§7).

`ValidationContext` reúne todo lo que las capas necesitan y que el
sistema tiene *antes* de validar un componente: el `ProblemModel` (ya
validado o en validación), micro-instancias, soluciones factibles
triviales (§6.4: el LLM también las genera) y presupuestos.

`ValidationReport.feedback()` produce el texto que se devuelve al LLM
para la iteración de corrección (§6: "el error o la propiedad violada
se devuelve al LLM").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

LAYERS = ("syntactic", "contractual", "semantic_mip", "operational", "quality")


@dataclass
class CheckResult:
    layer: str
    name: str
    passed: bool
    message: str = ""

    def __str__(self) -> str:
        mark = "OK " if self.passed else "FAIL"
        return f"[{mark}] {self.layer}/{self.name}" + (f": {self.message}" if self.message else "")


@dataclass
class ValidationReport:
    subject: str
    results: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    def extend(self, results: Sequence[CheckResult]) -> None:
        self.results.extend(results)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed_layer(self) -> str | None:
        for layer in LAYERS:
            if any(not r.passed and r.layer == layer for r in self.results):
                return layer
        return None

    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    def feedback(self) -> str:
        """Texto para el LLM: qué propiedad se violó y en qué capa."""
        if self.passed:
            return f"{self.subject}: todas las verificaciones pasaron ({len(self.results)} checks)."
        lines = [f"{self.subject}: rechazado en la capa '{self.failed_layer}'. Propiedades violadas:"]
        for r in self.failures():
            lines.append(f"  - {r.name}: {r.message}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return "\n".join(str(r) for r in self.results)


@dataclass
class ValidationContext:
    """Todo lo que las capas necesitan para ejercitar un componente."""

    problem: Any  # ProblemModel
    instances: list[Any]  # micro-instancias
    trivial_solutions: list[Any]  # una solución factible por micro-instancia
    seeds: tuple[int, ...] = (0, 1, 2)
    tolerance: float = 1e-6
    mip_time_limit: float = 5.0
    max_moves_checked: int = 50
    # Si el problema penaliza infactibilidad en vez de rechazarla, los movimientos
    # pueden producir soluciones infactibles legítimamente: no se exige factibilidad.
    require_feasible_moves: bool = False
    # Necesarios para validar algunos slots en contexto (p.ej. repair_mip usa una
    # destrucción para elegir free_vars; evaluator usa un vecindario para `incremental`).
    reference_destruction: Any = None
    reference_neighborhood: Any = None
    # Constructor aleatorio de referencia para la capa de calidad mínima.
    baseline_constructor: Any = None
    # Si True, un vecindario debe tener movimientos de mejora desde las soluciones de
    # PARTIDA (trivial / constructor), no solo desde soluciones aleatorias. Se activa al
    # generar con LLM (empuja al modelo a operadores útiles desde donde arranca el
    # esqueleto); se deja en False al admitir al catálogo, porque un operador estrecho
    # puede valer en combinación (VNS, ILS) y eso lo decide el tuning.
    require_improving_from_start: bool = False
    # Cuánto peor que la solución trivial de referencia se tolera a un constructor. La
    # referencia puede ser Relax-and-Fix (basada en MIP) en instancias donde lot-for-lot
    # es infactible, así que exigir cerca de ella es exigirle calidad de matheurística a
    # un greedy: el constructor solo tiene que ser un punto de partida usable.
    constructor_max_relative_gap: float = 1.0
    # Componentes del mismo slot YA aceptados, como (nombre, impl). El gate de diversidad
    # rechaza un componente estructuralmente equivalente a uno de estos: exigir mejora
    # desde la partida embudona al modelo hacia el único operador que funciona
    # (corrida 5: Jaccard 0,75–1,00 entre los tres "vecindarios distintos").
    accepted_peers: list = field(default_factory=list)
    max_similarity_to_peers: float = 0.8
    # Opcional: enumerador de todas las soluciones de una micro-instancia
    # (para comparar el óptimo del MIP contra fuerza bruta).
    enumerate_solutions: Callable[[Any], Sequence[Any]] | None = None

    def variables(self, inst) -> set[str]:
        groups = self.problem.variable_groups(inst)
        return {v for vs in groups.values() for v in vs}


def ok(layer: str, name: str, message: str = "") -> CheckResult:
    return CheckResult(layer, name, True, message)


def fail(layer: str, name: str, message: str) -> CheckResult:
    return CheckResult(layer, name, False, message)


def guard(layer: str, name: str, fn: Callable[[], CheckResult | list[CheckResult]]) -> list[CheckResult]:
    """Ejecuta un check convirtiendo excepciones en FAIL con el traceback resumido."""
    try:
        result = fn()
        return result if isinstance(result, list) else [result]
    except Exception as exc:  # noqa: BLE001 — queremos capturar cualquier error del componente
        return [fail(layer, name, f"excepción {type(exc).__name__}: {exc}")]
