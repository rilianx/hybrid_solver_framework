"""Contratos (Protocols) de `ProblemModel` y de cada slot del esqueleto.

Estos son los tipos que el LLM debe respetar al generar componentes
(sección 4 de la propuesta) y el `ProblemModel` que actúa de puente
heurístico/matemático (sección 3). Son intencionalmente genéricos:
cada problema concreto (ver `examples/knapsack`) instancia `Solution`,
`Instance`, `Move` y `MIPModel` con sus propios tipos.

No hay lógica de negocio aquí: solo la forma que el validador (capa
sintáctica, `core.validation`) y el ensamblador (`core.skeleton`)
asumen que cualquier componente va a tener.
"""

from __future__ import annotations

from random import Random
from typing import Any, Iterable, Protocol, runtime_checkable

# Alias genéricos. Cada problema concreto los especializa; el núcleo
# los trata como opacos (duck typing total).
Solution = Any
Instance = Any
Move = Any
MIPModel = Any


@runtime_checkable
class ProblemModel(Protocol):
    """Único módulo que conoce las dos vistas de la solución (§3).

    Generado y validado por-problema. Es el "puente" entre la vista
    estructural (para heurísticas) y la vista de asignación de
    variables (para el sub-MIP).
    """

    def load(self, path: str) -> Instance: ...

    def is_feasible(self, sol: Solution) -> bool: ...

    def objective(self, sol: Solution) -> float: ...

    # --- Puente hacia lo matemático ---
    def build_mip(self, inst: Instance) -> MIPModel: ...

    def to_assignment(self, sol: Solution) -> dict[str, float]: ...

    def from_assignment(self, x: dict[str, float]) -> Solution: ...

    def variable_groups(self, inst: Instance) -> dict[str, list[str]]: ...


@runtime_checkable
class Constructor(Protocol):
    """Slot `constructor`: produce una solución inicial factible."""

    def build(self, inst: Instance, rng: Random) -> Solution: ...


@runtime_checkable
class Neighborhood(Protocol):
    """Slot `neighborhood`: movimientos locales con delta incremental.

    Propiedad verificable: ``undo(apply(sol, m)) == sol`` y
    ``delta(sol, m) == f(apply(sol, m)) - f(sol)``.
    """

    def moves(self, sol: Solution) -> Iterable[Move]: ...

    def apply(self, sol: Solution, m: Move) -> Solution: ...

    def undo(self, sol: Solution, m: Move) -> Solution: ...

    def delta(self, sol: Solution, m: Move) -> float: ...


@runtime_checkable
class Evaluator(Protocol):
    """Slot `evaluator`: evaluación completa e incremental."""

    def full(self, sol: Solution) -> float: ...

    def incremental(self, sol: Solution, m: Move) -> float: ...


@runtime_checkable
class Acceptance(Protocol):
    """Slot `acceptance`: decide si un candidato reemplaza a la solución actual."""

    def accept(self, f_cur: float, f_cand: float, state: "SearchStateLike") -> bool: ...


@runtime_checkable
class Memory(Protocol):
    """Slot `memory`: memoria de corto plazo (p.ej. lista tabú)."""

    def forbid(self, m: Move, state: "SearchStateLike") -> None: ...

    def is_tabu(self, m: Move, state: "SearchStateLike") -> bool: ...

    def aspiration(self, m: Move, f: float) -> bool: ...


@runtime_checkable
class Perturbation(Protocol):
    """Slot `perturbation`: kick heurístico (usado por ILS)."""

    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution: ...


@runtime_checkable
class Destruction(Protocol):
    """Slot `destruction`: elimina parte de la solución (usado por LNS/matheurísticas)."""

    def destroy(
        self, sol: Solution, ratio: float, rng: Random
    ) -> tuple[Any, set[str]]:
        """Retorna (parcial, free_vars) con free_vars ⊆ variables(inst)."""
        ...


@runtime_checkable
class RepairHeuristic(Protocol):
    """Slot `repair_heuristic`: reconstruye una solución factible tras destruir."""

    def repair(self, partial: Any, rng: Random) -> Solution: ...


@runtime_checkable
class RepairMIP(Protocol):
    """Slot `repair_mip`: resuelve un sub-MIP sobre las variables libres."""

    def repair_mip(
        self,
        model: MIPModel,
        fixed: dict[str, float],
        free_vars: set[str],
        time_limit: float,
        warm_start: dict[str, float] | None = None,
    ) -> Solution | None: ...


@runtime_checkable
class FixingPolicy(Protocol):
    """Slot `fixing_policy`: agenda de fijación/relajación (Relax-and-Fix, Fix-and-Optimize)."""

    def schedule(
        self, groups: dict[str, list[str]], params: Any
    ) -> Iterable[tuple[set[str], set[str], set[str]]]:
        """Itera (fix_set, integer_set, relax_set); debe cubrir todas las variables."""
        ...

    def blocks(self, groups: dict[str, list[str]], block_size: int) -> list[set[str]]: ...


@runtime_checkable
class StopCriterion(Protocol):
    """Slot `stop`: criterio de parada del esqueleto."""

    def stop(self, state: "SearchStateLike") -> bool: ...


@runtime_checkable
class SearchStateLike(Protocol):
    """Forma mínima del estado que ven Acceptance/Memory/StopCriterion.

    `core.skeleton.SearchState` es la implementación concreta; este
    Protocol existe para que los componentes puedan tipar su firma
    sin importar el módulo de esqueleto (evita ciclos de import).
    """

    iteration: int
    elapsed_time: float
    iters_without_improvement: int
    best_objective: float | None
    current_objective: float | None
    extra: dict[str, Any]
