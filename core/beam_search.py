"""Beam search constructiva sobre la `ConstructionView` (§5.1, estrategias constructivas).

    B ← {view.empty()}; mejor ← ∅
    mientras B no vacío y quede profundidad/tiempo:
        H ← ∅
        para cada parcial p en B:
            para cada acción a en expandir(p)            # todos los candidatos o los `branching` de menor puntaje
                q ← view.apply(p, a)
                si q completo: actualizar mejor con q; seguir
                v ← evaluar(q)                            # rollout greedy hasta el final | puntaje acumulado
                H ← H ∪ {(v, q)}
        B ← los `beam_width` de menor v en H (sin repetidos si la vista da `key`)
    devolver mejor

Dos formas de evaluar un parcial:

- `evaluation="rollout"` (*beam search greedy*, como BS-FRG de Araya y Toledo 2023, o el
  *pilot method* con `beam_width=1`): se completa el parcial con un greedy y el valor es el
  objetivo de la solución completa. Cada rollout es además una solución: la mejor de todas
  se conserva aunque su parcial salga del haz, así que el resultado nunca es peor que el
  greedy desde la raíz.
- `evaluation="score"` (beam search clásica): el valor es la suma de los puntajes de las
  acciones elegidas, sin completar; más barata, y solo produce soluciones al llegar a una
  hoja.

El rollout es un `GreedyScore` (se completa con `GreedyConstructor` y la regla `greedy`) o
`"complete"`, que usa `view.complete(parcial, rng)`: el respaldo del problema, cuando ese
respaldo es una heurística completa (FRG en el CPMP). Si la vista expone
`lower_bound(parcial)`, los parciales que no pueden mejorar a la mejor solución se podan.

`BeamSearchConstructor` cumple el `Protocol` `Constructor`: ocupa el slot `constructor`
de cualquier esqueleto, igual que `GreedyConstructor`.
"""

from __future__ import annotations

import math
import time
from random import Random
from typing import Any

from core.construction import GreedyConstructor

EVALUATIONS = ("rollout", "score")


class BeamSearchConstructor:
    def __init__(self, problem: Any, score: Any = None, rollout: Any = None, beam_width: int = 10,
                 branching: int | None = None, evaluation: str = "rollout", max_depth: int = 100_000,
                 max_seconds: float | None = None, dedup: bool = True, view_params: dict | None = None):
        """`score`: puntaje que ordena los hijos para `branching` y que suma `evaluation="score"`.
        `rollout`: `GreedyScore`, `"complete"` o None (el greedy de `score`, o `"complete"`
        si no hay puntaje). `branching`: hijos por parcial (None = todos los candidatos).
        `view_params`: se pasan a `problem.construction_view(inst, **view_params)` (p.ej. qué
        acciones ofrece la vista)."""
        if evaluation not in EVALUATIONS:
            raise ValueError(f"evaluación desconocida {evaluation!r}; opciones: {EVALUATIONS}")
        if evaluation == "score" and score is None:
            raise ValueError("evaluation='score' necesita un puntaje")
        if branching is not None and score is None:
            raise ValueError("branching necesita un puntaje para elegir los hijos")
        self.problem = problem
        self.score = score
        self.evaluation = evaluation
        self.beam_width = max(1, int(beam_width))
        self.branching = None if branching is None else max(1, int(branching))
        self.max_depth = max_depth
        self.max_seconds = max_seconds
        self.dedup = dedup
        self.view_params = dict(view_params or {})
        if rollout is None:
            rollout = score if score is not None else "complete"
        self.rollout = rollout
        self._greedy = None if rollout == "complete" else GreedyConstructor(problem, rollout)
        self.builds = 0
        self.rollouts = 0
        self.levels = 0

    # --- evaluación -------------------------------------------------------------------
    def _complete(self, view, partial, rng: Random):
        self.rollouts += 1
        if self._greedy is None:
            return view.complete(partial, rng)
        return self._greedy.complete_from(view, partial, rng)[0]

    def _value(self, sol) -> float:
        P = self.problem
        return float(P.objective(sol)) if P.is_feasible(sol) else math.inf

    # --- búsqueda ---------------------------------------------------------------------
    def build(self, inst: Any, rng: Random):
        view = self.problem.construction_view(inst, **self.view_params)
        self.builds += 1
        t0 = time.perf_counter()
        bound = getattr(view, "lower_bound", None)
        key = getattr(view, "key", None) if self.dedup else None

        root = view.empty()
        if view.is_complete(root):
            return view.to_solution(root)
        best = self._complete(view, root, rng) if self.evaluation == "rollout" else None
        best_v = self._value(best) if best is not None else math.inf
        beam = [(0.0, root)]  # (puntaje acumulado, parcial)

        for depth in range(self.max_depth):
            if not beam or (self.max_seconds is not None and time.perf_counter() - t0 > self.max_seconds):
                break
            self.levels = depth + 1
            children: list[tuple[float, int, float, Any]] = []  # (valor, orden, acumulado, parcial)
            seen: set = set()
            for acc, p in beam:
                cands = list(view.candidates(p))
                if not cands:
                    continue
                if self.score is not None:
                    scores = [float(self.score.score(p, c)) for c in cands]
                    order = sorted(range(len(cands)), key=scores.__getitem__)
                    if self.branching is not None:
                        order = order[: self.branching]
                    expand = [(cands[i], scores[i]) for i in order]
                else:
                    expand = [(c, 0.0) for c in cands]
                for a, s in expand:
                    q = view.apply(p, a)
                    if key is not None:
                        k = key(q)
                        if k in seen:
                            continue
                        seen.add(k)
                    if view.is_complete(q):
                        sol = view.to_solution(q)
                        v = self._value(sol)
                        if v < best_v:
                            best, best_v = sol, v
                        continue
                    if bound is not None and bound(q) >= best_v:
                        continue
                    if self.evaluation == "rollout":
                        sol = self._complete(view, q, rng)
                        v = self._value(sol)
                        if v < best_v:
                            best, best_v = sol, v
                    else:
                        v = acc + s
                    children.append((v, len(children), acc + s, q))
            children.sort(key=lambda c: (c[0], c[1]))
            beam = [(acc, q) for _, _, acc, q in children[: self.beam_width]]

        if best is None:  # evaluation="score" sin llegar a ninguna hoja: se completa el mejor del haz
            start = beam[0][1] if beam else root
            best = self._greedy.complete_from(view, start, rng)[0] if self._greedy else view.complete(start, rng)
        return best


__all__ = ["BeamSearchConstructor", "EVALUATIONS"]
