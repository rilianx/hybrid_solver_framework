"""Componentes heurísticos para el CLSP (lo que generaría el LLM, §6).

Lo relevante frente a knapsack: la **destrucción por ventana de períodos**
usa la estructura temporal (`variable_groups`), que es exactamente el tipo
de componente "matemático específico del problema" que la propuesta
espera del LLM (destruir períodos consecutivos, §6.3).
"""

from __future__ import annotations

from random import Random

from .problem_model import CLSPInstance, LotSizingModel, Solution, var_name


class LotForLotConstructor:
    """Setup en cada período con demanda positiva (sin inventario)."""

    def build(self, inst: CLSPInstance, rng: Random) -> Solution:
        return tuple(tuple(d > 0 for d in row) for row in inst.demand)


COMPONENT_LOT_FOR_LOT = {
    "name": "lot_for_lot",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "LNS_MIP", "FIX_OPT"],
    "params": {},
}


class SetupFlipNeighborhood:
    """Invierte un setup y[i][t]. `delta` evalúa vía el LP cacheado del modelo."""

    def __init__(self, problem: LotSizingModel):
        self.problem = problem

    def moves(self, sol: Solution):
        for i in range(len(sol)):
            for t in range(len(sol[i])):
                yield (i, t)

    def apply(self, sol: Solution, m) -> Solution:
        i, t = m
        row = sol[i][:t] + (not sol[i][t],) + sol[i][t + 1 :]
        return sol[:i] + (row,) + sol[i + 1 :]

    def undo(self, sol: Solution, m) -> Solution:
        return self.apply(sol, m)  # el flip es su propia inversa

    def delta(self, sol: Solution, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)

    def describe_move(self, sol: Solution, m) -> str:
        i, t = m
        return f"{'APAGAR' if sol[i][t] else 'ENCENDER'} el setup del ítem {i} en el período {t}"


COMPONENT_SETUP_FLIP = {
    "name": "setup_flip",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class SetupFlipPerturbation:
    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution:
        rows = [list(r) for r in sol]
        n_i, n_t = len(rows), len(rows[0])
        for _ in range(max(1, int(round(strength)))):
            i, t = rng.randrange(n_i), rng.randrange(n_t)
            rows[i][t] = not rows[i][t]
        return tuple(tuple(r) for r in rows)


COMPONENT_SETUP_FLIP_PERTURBATION = {
    "name": "setup_flip_perturbation",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "params": {"strength": {"type": "int", "range": [1, 6]}},
}


class PeriodWindowDestruction:
    """Libera todos los setups de una ventana de períodos consecutivos.

    `ratio` se traduce a ancho de ventana: `max(1, round(ratio * T))`.
    Es la destrucción "relacionada" natural de un problema con estructura
    temporal; comparar contra la aleatoria es una de las preguntas de §10.
    """

    def __init__(self, inst: CLSPInstance):
        self.inst = inst

    def destroy(self, sol: Solution, ratio: float, rng: Random):
        T = self.inst.n_periods
        width = max(1, min(T, int(round(ratio * T))))
        start = rng.randint(0, T - width)
        free_vars = {var_name(i, t) for i in range(self.inst.n_items) for t in range(start, start + width)}
        partial = {
            var_name(i, t): float(sol[i][t])
            for i in range(self.inst.n_items)
            for t in range(T)
            if not (start <= t < start + width)
        }
        return partial, free_vars


COMPONENT_PERIOD_WINDOW_DESTRUCTION = {
    "name": "period_window_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.variable_groups"],
    "params": {"ratio": {"type": "float", "range": [0.1, 0.6]}},
}


class RandomSetupDestruction:
    def __init__(self, inst: CLSPInstance):
        self.inst = inst

    def destroy(self, sol: Solution, ratio: float, rng: Random):
        names = [var_name(i, t) for i in range(self.inst.n_items) for t in range(self.inst.n_periods)]
        k = max(1, int(round(ratio * len(names))))
        free_vars = set(rng.sample(names, k))
        partial = {
            var_name(i, t): float(sol[i][t])
            for i in range(self.inst.n_items)
            for t in range(self.inst.n_periods)
            if var_name(i, t) not in free_vars
        }
        return partial, free_vars


COMPONENT_RANDOM_SETUP_DESTRUCTION = {
    "name": "random_setup_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.5]}},
}
