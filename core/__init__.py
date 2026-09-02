"""Núcleo del framework de solvers híbridos.

Expone los Protocols de slots, el ProblemModel, el esqueleto genérico
de trayectoria y el registro de componentes (metadatos + validación
de compatibilidad), tal como se describe en las secciones 2-4 de la
propuesta `propuesta_solvers_hibridos_llm.md`.
"""

from .contracts import (
    Solution,
    Instance,
    Move,
    MIPModel,
    ProblemModel,
    Constructor,
    Neighborhood,
    Evaluator,
    Acceptance,
    Memory,
    Perturbation,
    Destruction,
    RepairHeuristic,
    RepairMIP,
    FixingPolicy,
    StopCriterion,
)
from .component import ComponentSpec, ComponentRegistry
from .skeleton import TrajectorySkeleton, SearchState, RunResult

__all__ = [
    "Solution",
    "Instance",
    "Move",
    "MIPModel",
    "ProblemModel",
    "Constructor",
    "Neighborhood",
    "Evaluator",
    "Acceptance",
    "Memory",
    "Perturbation",
    "Destruction",
    "RepairHeuristic",
    "RepairMIP",
    "FixingPolicy",
    "StopCriterion",
    "ComponentSpec",
    "ComponentRegistry",
    "TrajectorySkeleton",
    "SearchState",
    "RunResult",
]
