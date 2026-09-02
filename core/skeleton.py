"""Esqueleto genérico de trayectoria (§2 de la propuesta).

    solución ← CONSTRUCTOR(instancia)
    mejor    ← solución
    mientras no PARADA():
        candidato ← GENERADOR_CANDIDATO(solución)
        si ACEPTACION(solución, candidato): solución ← candidato
        si f(solución) < f(mejor): mejor ← solución
        ESTADO.actualizar()
    retornar mejor

`TrajectorySkeleton` es la única clase de "bucle de control" del
núcleo: SA, ILS y LNS-MIP (`skeletons/`) no reimplementan el bucle,
solo construyen el `candidate_generator` y los `state_updaters`
correctos a partir de los componentes que reciben en sus slots. Esto
es literalmente la idea central de la sección 2: menos esqueletos,
más combinaciones por composición.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from random import Random
from typing import Any, Callable, Optional

from .contracts import Acceptance, ProblemModel, Solution, StopCriterion

# GENERADOR_CANDIDATO: (solución_actual, estado, rng) -> candidato (o None si no hay candidato válido)
CandidateGenerator = Callable[[Solution, "SearchState", Random], Optional[Solution]]

# ESTADO.actualizar(): función que muta el estado in-place tras cada iteración
# (p.ej. enfriar temperatura, avanzar k de VNS, adaptar destroy_ratio).
StateUpdater = Callable[["SearchState"], None]


@dataclass
class SearchState:
    """Estado compartido que ven Acceptance/Memory/StopCriterion/StateUpdaters.

    `extra` es el espacio libre donde cada esqueleto guarda su estado
    propio (temperatura en SA, lista tabú en TS, índice k en VNS,
    destroy_ratio adaptativo en LNS-MIP, ...) sin que el bucle genérico
    necesite conocerlo.
    """

    iteration: int = 0
    elapsed_time: float = 0.0
    iters_without_improvement: int = 0
    best_objective: float | None = None
    current_objective: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    _start_time: float = field(default_factory=time.monotonic, repr=False, compare=False)

    def tick(self) -> None:
        self.iteration += 1
        self.elapsed_time = time.monotonic() - self._start_time


@dataclass
class RunResult:
    best_solution: Solution
    best_objective: float
    iterations: int
    elapsed_time: float
    accepted: int
    history: list[float] = field(default_factory=list)


class TrajectorySkeleton:
    """Motor de trayectoria genérico, parametrizado por componentes.

    Los esqueletos concretos (SA, ILS, LNS-MIP, ...) son *configuraciones*
    de esta clase: fijan `candidate_generator`, `state_updaters` y el
    estado inicial en `extra`, pero el bucle `run()` es siempre el mismo.
    """

    def __init__(
        self,
        problem: ProblemModel,
        constructor,
        candidate_generator: CandidateGenerator,
        acceptance: Acceptance,
        stop: StopCriterion,
        state_updaters: list[StateUpdater] | None = None,
        record_history: bool = False,
    ) -> None:
        self.problem = problem
        self.constructor = constructor
        self.candidate_generator = candidate_generator
        self.acceptance = acceptance
        self.stop = stop
        self.state_updaters = state_updaters or []
        self.record_history = record_history

    def run(self, inst: Any, rng: Random, initial_extra: dict[str, Any] | None = None) -> RunResult:
        sol = self.constructor.build(inst, rng)
        f_sol = self.problem.objective(sol)
        best, f_best = sol, f_sol

        state = SearchState(
            current_objective=f_sol,
            best_objective=f_best,
            extra=dict(initial_extra or {}),
        )
        history: list[float] = [f_best] if self.record_history else []
        accepted = 0

        while not self.stop.stop(state):
            candidate = self.candidate_generator(sol, state, rng)
            if candidate is not None:
                f_cand = self.problem.objective(candidate)
                if self.acceptance.accept(f_sol, f_cand, state):
                    sol, f_sol = candidate, f_cand
                    accepted += 1
                    state.current_objective = f_sol
                    if f_sol < f_best:
                        best, f_best = sol, f_sol
                        state.best_objective = f_best
                        state.iters_without_improvement = 0
                    else:
                        state.iters_without_improvement += 1
                else:
                    state.iters_without_improvement += 1
            else:
                state.iters_without_improvement += 1

            for updater in self.state_updaters:
                updater(state)

            state.tick()
            if self.record_history:
                history.append(f_best)

        return RunResult(
            best_solution=best,
            best_objective=f_best,
            iterations=state.iteration,
            elapsed_time=state.elapsed_time,
            accepted=accepted,
            history=history,
        )
