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


class GreedyConstructor:
    def __init__(self, problem: Any, score: Any, rule: str = "greedy", alpha: float = 0.2, max_steps: int = 100_000):
        if rule not in RULES:
            raise ValueError(f"regla desconocida {rule!r}; opciones: {RULES}")
        self.problem = problem
        self.score = score
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
        partial, chosen = view.empty(), []
        for _ in range(self.max_steps):
            if view.is_complete(partial):
                return view.to_solution(partial), chosen
            cands = list(view.candidates(partial))
            if not cands:
                self.fallbacks += 1
                return view.complete(partial, rng), chosen
            scores = [float(self.score.score(partial, c)) for c in cands]
            if any(math.isnan(s) or math.isinf(s) for s in scores):
                raise ValueError("el puntaje devolvió NaN o infinito")
            action = self._pick(cands, scores, rng)
            chosen.append(action)
            partial = view.apply(partial, action)
        raise RuntimeError(f"la construcción no terminó en {self.max_steps} pasos")


__all__ = ["GreedyConstructor", "RULES"]
