"""SA (Simulated Annealing) como configuración del esqueleto genérico (§5.1).

Slots obligatorios: Constructor, Vecindario, Evaluador, Aceptación
(Metropolis). Estado propio: temperatura. Parámetros del esqueleto:
`T0`, `alpha`, `iters_per_T`.

No hay ningún bucle nuevo aquí: `build_sa` solo arma el
`candidate_generator` (mover aleatoriamente en el vecindario) y el
`state_updater` de enfriamiento, y delega la ejecución a
`TrajectorySkeleton`.
"""

from __future__ import annotations

import math
from random import Random

from core.contracts import Acceptance, Constructor, Neighborhood, ProblemModel, StopCriterion
from core.skeleton import SearchState, TrajectorySkeleton


class MetropolisAcceptance:
    """Aceptación de Metropolis estándar: siempre si mejora, si no con prob. exp(-Δ/T)."""

    def accept(self, f_cur: float, f_cand: float, state: SearchState) -> bool:
        delta = f_cand - f_cur
        if delta <= 0:
            return True
        temperature = state.extra.get("temperature", 1e-9)
        if temperature <= 0:
            return False
        # rng determinístico por-llamada vía state.extra para no romper el contrato
        # Acceptance(f_cur, f_cand, state) -> bool (sin rng explícito).
        rng: Random = state.extra["rng"]
        return rng.random() < math.exp(-delta / temperature)


def _cooling_updater(alpha: float, iters_per_T: int):
    def _update(state: SearchState) -> None:
        state.extra["_iters_at_T"] = state.extra.get("_iters_at_T", 0) + 1
        if state.extra["_iters_at_T"] >= iters_per_T:
            state.extra["temperature"] *= alpha
            state.extra["_iters_at_T"] = 0

    return _update


def build_sa(
    problem: ProblemModel,
    constructor: Constructor,
    neighborhood: Neighborhood,
    stop: StopCriterion,
    T0: float = 10.0,
    alpha: float = 0.95,
    iters_per_T: int = 1,
    acceptance: Acceptance | None = None,
    record_history: bool = False,
) -> tuple[TrajectorySkeleton, dict]:
    """Retorna (skeleton, initial_extra) listos para `skeleton.run(inst, rng, initial_extra)`."""

    acceptance = acceptance or MetropolisAcceptance()

    def candidate_generator(sol, state: SearchState, rng: Random):
        moves = list(neighborhood.moves(sol))
        if not moves:
            return None
        m = rng.choice(moves)
        return neighborhood.apply(sol, m)

    skeleton = TrajectorySkeleton(
        problem=problem,
        constructor=constructor,
        candidate_generator=candidate_generator,
        acceptance=acceptance,
        stop=stop,
        state_updaters=[_cooling_updater(alpha, iters_per_T)],
        record_history=record_history,
    )

    # `rng` se inyecta también en extra porque el contrato `Acceptance.accept`
    # (§4) no recibe rng explícito; así Metropolis puede muestrear sin romper
    # la firma común a todos los componentes de aceptación.
    initial_extra = {"temperature": T0}
    return skeleton, initial_extra


def make_run(skeleton: TrajectorySkeleton, initial_extra: dict):
    """Envuelve `skeleton.run` para inyectar `rng` en `state.extra` (ver nota arriba)."""

    def run(inst, rng: Random):
        extra = dict(initial_extra)
        extra["rng"] = rng
        return skeleton.run(inst, rng, initial_extra=extra)

    return run
