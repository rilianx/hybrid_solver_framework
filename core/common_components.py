"""Componentes de propósito general, independientes del problema.

Estos no los genera el LLM (o si los genera, son el ejemplo few-shot
de referencia): aceptación y parada son casi siempre las mismas pocas
variantes, así que vale la pena tenerlas en el núcleo en vez de
regenerarlas por cada problema piloto.
"""

from __future__ import annotations

from dataclasses import dataclass

from .skeleton import SearchState


class BetterAcceptance:
    """Acepta solo si el candidato mejora estrictamente (usado por HC / LNS-MIP conservador)."""

    def accept(self, f_cur: float, f_cand: float, state: SearchState) -> bool:
        return f_cand < f_cur


class AlwaysAccept:
    """Acepta siempre el candidato (random walk; útil como baseline de Aceptación en ILS)."""

    def accept(self, f_cur: float, f_cand: float, state: SearchState) -> bool:
        return True


@dataclass
class ThresholdAccept:
    """Acepta si el candidato no empeora más allá de un umbral absoluto (Threshold Accepting)."""

    threshold: float = 0.0

    def accept(self, f_cur: float, f_cand: float, state: SearchState) -> bool:
        return f_cand <= f_cur + self.threshold


@dataclass
class MaxIterationsStop:
    max_iterations: int

    def stop(self, state: SearchState) -> bool:
        return state.iteration >= self.max_iterations


@dataclass
class MaxTimeStop:
    max_seconds: float

    def stop(self, state: SearchState) -> bool:
        return state.elapsed_time >= self.max_seconds


@dataclass
class MaxIterationsWithoutImprovementStop:
    patience: int

    def stop(self, state: SearchState) -> bool:
        return state.iters_without_improvement >= self.patience


class MIPModelRepair:
    """Reparación MIP genérica (slot `repair_mip`) para cualquier `ProblemModel`
    cuyo `build_mip` devuelva un `core.mip.MIPModel`: libera `free_vars` como
    enteras, fija el resto y traduce la asignación con `from_assignment`."""

    def __init__(self, problem):
        self.problem = problem

    def repair_mip(self, model, fixed, free_vars, time_limit, warm_start=None):
        x = model.solve(fixed=fixed, integer=set(free_vars), relaxed=set(), time_limit=time_limit, warm_start=warm_start)
        return None if x is None else self.problem.from_assignment(x)


@dataclass
class AnyStop:
    """Combina varios criterios de parada con OR (para el ejemplo, "lo que ocurra primero")."""

    criteria: tuple

    def stop(self, state: SearchState) -> bool:
        return any(c.stop(state) for c in self.criteria)
