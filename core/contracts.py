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

    # Opcionales (no forman parte del Protocol; el núcleo los usa si existen):
    #   construction_view(inst)   vista constructiva para el constructor modular (`core.construction`)
    #   random_solution(rng)      solución al azar con estructura válida, para validar vecindarios lejos de
    #                             la partida cuando una asignación 0/1 al azar no es una solución (CVRP)
    #   explain_infeasibility(sol), validation_hints   texto para el feedback del validador


@runtime_checkable
class Constructor(Protocol):
    """Slot `constructor`: produce una solución inicial factible."""

    def build(self, inst: Instance, rng: Random) -> Solution: ...


Partial = Any  # estado parcial de una construcción
Action = Any  # acción constructiva


@runtime_checkable
class ConstructionView(Protocol):
    """Vista constructiva del problema: la parte del `ProblemModel` que un constructor
    greedy necesita (`problem.construction_view(inst)`). El bucle y la regla de selección
    son del framework (`core.construction`); lo único que se enchufa es el puntaje.

    `candidates` debe devolver solo acciones que no cierran la puerta a completar una
    solución factible, hasta donde el problema permita verificarlo barato. Cuando no
    quedan candidatos sin haber terminado (callejón sin salida), `complete` cierra la
    construcción con un respaldo propio del problema.
    """

    def empty(self) -> Partial: ...

    def candidates(self, partial: Partial) -> Iterable[Action]: ...

    def apply(self, partial: Partial, action: Action) -> Partial: ...

    def is_complete(self, partial: Partial) -> bool: ...

    def to_solution(self, partial: Partial) -> Solution: ...

    def complete(self, partial: Partial, rng: Random) -> Solution: ...


@runtime_checkable
class GreedyScore(Protocol):
    """Slot `greedy_score`: puntúa una acción constructiva; MENOR es mejor. Debe ser
    barato (se llama para cada candidato en cada paso), determinista y no modificar
    `partial`. No decide factibilidad: los candidatos ya vienen filtrados."""

    def score(self, partial: Partial, action: Action) -> float: ...


Memory = Any  # memoria de una política constructiva (inmutable y hashable)


@runtime_checkable
class ConstructionPolicy(Protocol):
    """Slot `construction_policy`: un puntaje CON MEMORIA. Un `greedy_score` solo ve
    (parcial, acción) y no puede sostener un plan de varios pasos; muchas heurísticas
    constructivas sí lo hacen (FRG en el CPMP: "estoy vaciando la pila s y cada contenedor ya
    tiene destino asignado"). La memoria viaja junto al parcial: el greedy la actualiza con la
    acción elegida y la beam search, en cada hijo, con la acción de ese hijo (aunque la
    política no la hubiera elegido: ahí la política decide si abandona su plan).

    `score` es MENOR = mejor, determinista, y no modifica ni `partial` ni `memory`; `update`
    devuelve la memoria nueva sin modificar la anterior. La memoria debe ser inmutable y
    hashable (una tupla, un frozenset, un dataclass frozen)."""

    def init(self, partial: Partial) -> Memory: ...

    def score(self, partial: Partial, memory: Memory, action: Action) -> float: ...

    def update(self, partial: Partial, memory: Memory, action: Action) -> Memory: ...


@runtime_checkable
class Neighborhood(Protocol):
    """Slot `neighborhood`: movimientos locales con delta incremental.

    Propiedad verificable: ``delta(sol, m) == f(apply(sol, m)) - f(sol)``.

    Sin `undo`: las soluciones son inmutables, así que el esqueleto conserva la anterior y ningún
    esqueleto deshace movimientos. Era la mayor fuente de rechazos de los vecindarios generados
    (corridas 36, 37 y 39) sin que se usara en ningún lado; si un componente lo define, se verifica
    ``undo(apply(sol, m), m) == sol``.
    """

    def moves(self, sol: Solution) -> Iterable[Move]: ...

    def apply(self, sol: Solution, m: Move) -> Solution: ...

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
