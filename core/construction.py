"""Constructor greedy genérico: el bucle y la regla de selección son del framework.

    parcial ← view.empty()
    mientras no view.is_complete(parcial):
        C ← view.candidates(parcial)
        si C vacío: devolver view.complete(parcial, rng)       # callejón sin salida
        c ← seleccionar(C, score.score(parcial, ·), rng)        # greedy | rcl | roulette
        parcial ← view.apply(parcial, c)
    devolver view.to_solution(parcial)

`GreedyConstructor` cumple el `Protocol` `Constructor`, así que ocupa el slot
`constructor` de cualquier esqueleto. Lo que cambia entre constructores es solo el
`GreedyScore` (slot `greedy_score`, lo que genera el LLM) y la regla:

- `greedy`: el de menor puntaje (empates por orden de los candidatos);
- `rcl`: lista restringida de candidatos de GRASP, los de puntaje ≤ mín + α·(máx − mín),
  y uno al azar entre ellos (α = 0 es greedy, α = 1 es al azar);
- `roulette`: probabilidad proporcional a 1 / (puntaje − mín + ε).

El criterio puede ser un `GreedyScore` (sin memoria) o una `ConstructionPolicy` (slot
`construction_policy`: `init`, `score(parcial, memoria, acción)`, `update`), que sostiene un
plan de varios pasos; `as_policy` adapta el primero al segundo, así que el bucle es uno solo.

La factibilidad es responsabilidad de la vista (`ConstructionView.candidates` y
`complete`), no del puntaje: un puntaje malo da una solución mala, no una infactible
hasta donde la vista la pueda garantizar. `fallbacks` cuenta cuántas construcciones
terminaron en `complete`.
"""

from __future__ import annotations

import math
from random import Random
from typing import Any

RULES = ("greedy", "rcl", "roulette")


def is_policy(obj: Any) -> bool:
    return callable(getattr(obj, "init", None)) and callable(getattr(obj, "update", None))


class _Stateless:
    """Un `GreedyScore` visto como política sin memoria."""

    def __init__(self, score: Any):
        self.inner = score

    def init(self, partial: Any):
        return None

    def score(self, partial: Any, memory: Any, action: Any) -> float:
        return self.inner.score(partial, action)

    def update(self, partial: Any, memory: Any, action: Any):
        return None


def as_policy(obj: Any) -> Any:
    return obj if is_policy(obj) else _Stateless(obj)


class GreedyConstructor:
    def __init__(self, problem: Any, score: Any, rule: str = "greedy", alpha: float = 0.2, max_steps: int = 100_000):
        if rule not in RULES:
            raise ValueError(f"regla desconocida {rule!r}; opciones: {RULES}")
        self.problem = problem
        self.score = score
        self.policy = as_policy(score)
        self.rule = rule
        self.alpha = float(alpha)
        self.max_steps = max_steps
        self.builds = 0
        self.fallbacks = 0

    def _pick(self, cands: list, scores: list[float], rng: Random):
        if self.rule == "greedy":
            return cands[min(range(len(cands)), key=scores.__getitem__)]
        lo, hi = min(scores), max(scores)
        if self.rule == "rcl":
            cut = lo + self.alpha * (hi - lo)
            pool = [c for c, s in zip(cands, scores) if s <= cut + 1e-12]
            return pool[rng.randrange(len(pool))]
        eps = 1e-9 + 1e-6 * (hi - lo)
        weights = [1.0 / (s - lo + eps) for s in scores]
        r, acc = rng.random() * sum(weights), 0.0
        for c, w in zip(cands, weights):
            acc += w
            if acc >= r:
                return c
        return cands[-1]

    def build(self, inst: Any, rng: Random):
        return self.trace(inst, rng)[0]

    def trace(self, inst: Any, rng: Random) -> tuple[Any, list]:
        """(solución, acciones elegidas en orden). La secuencia de acciones es la firma que
        usa el gate de diversidad para comparar puntajes."""
        view = self.problem.construction_view(inst)
        self.builds += 1
        sol, chosen, fell_back = self.complete_from(view, view.empty(), rng)
        self.fallbacks += fell_back
        return sol, chosen

    def complete_from(self, view: Any, partial: Any, rng: Random, memory: Any = None,
                      fresh: bool = True) -> tuple[Any, list, bool]:
        """Completa `partial` con el bucle greedy: (solución, acciones, ¿terminó en el
        respaldo?). Es el *rollout* que usa la beam search para evaluar un parcial. `memory`:
        la de la política en `partial` (con `fresh`, se empieza con `policy.init(partial)`)."""
        if fresh:
            memory = self.policy.init(partial)
        chosen: list = []
        for _ in range(self.max_steps):
            if view.is_complete(partial):
                return view.to_solution(partial), chosen, False
            cands = list(view.candidates(partial))
            if not cands:
                return view.complete(partial, rng), chosen, True
            action = self._pick(cands, self.scores(partial, cands, memory), rng)
            chosen.append(action)
            memory = self.policy.update(partial, memory, action)
            partial = view.apply(partial, action)
        raise RuntimeError(f"la construcción no terminó en {self.max_steps} pasos")

    def scores(self, partial: Any, cands: list, memory: Any = None) -> list[float]:
        scores = [float(self.policy.score(partial, memory, c)) for c in cands]
        if any(math.isnan(s) or math.isinf(s) for s in scores):
            raise ValueError("el puntaje devolvió NaN o infinito")
        return scores


__all__ = ["GreedyConstructor", "RULES"]
