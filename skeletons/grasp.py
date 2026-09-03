"""GRASP+LS como configuración del esqueleto genérico (§5.1).

Slots: Constructor aleatorizado, LS interno, Parada. Cada iteración es un
reinicio: construir una solución nueva (con el rng) y mejorarla con la
búsqueda local; se conserva la mejor. En el bucle genérico esto es un
`candidate_generator` que ignora la solución actual, con `BetterAcceptance`
para que `sol` siga siendo la mejor encontrada.

Para que tenga sentido, el constructor debe ser realmente aleatorizado
(p.ej. GRASP con RCL, o cualquier constructor que use `rng`); con un
constructor determinista degenera en "construir una vez + LS".
"""

from __future__ import annotations

from random import Random

from core.common_components import BetterAcceptance
from core.contracts import Constructor, Neighborhood, ProblemModel, StopCriterion
from core.skeleton import SearchState, TrajectorySkeleton
from skeletons.ils import LocalSearch, hill_climb


def build_grasp(
    problem: ProblemModel,
    constructor: Constructor,
    neighborhood: Neighborhood,
    stop: StopCriterion,
    local_search: LocalSearch | None = None,
    ls_strategy: str = "first",
    ls_max_seconds: float | None = None,
    record_history: bool = False,
) -> TrajectorySkeleton:
    ls = local_search or hill_climb(problem, neighborhood, strategy=ls_strategy, max_seconds=ls_max_seconds)

    def candidate_generator(sol, state: SearchState, rng: Random):
        return ls(constructor.build(state.extra["_inst"], rng), rng)

    return TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=BetterAcceptance(),
        stop=stop,
        record_history=record_history,
    )


def run_grasp(skeleton: TrajectorySkeleton, inst, rng: Random):
    return skeleton.run(inst, rng, initial_extra={"_inst": inst})
