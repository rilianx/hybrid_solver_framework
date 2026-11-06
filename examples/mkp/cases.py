"""Casos de prueba de la mochila multidimensional al estilo Codeforces (`cases.json`): micro-instancias con respuestas
conocidas, para validar un modelo generado (`core.validation.model_parts`).

    python -m examples.mkp.cases        # regenera cases.json

Cada caso trae la instancia en el formato de entrada (`MKPInstance.to_text`), soluciones en el formato neutral (0/1 por
ítem, en una lista de una lista) con su factibilidad, la familia violada o el costo (el beneficio con signo menos), y
el óptimo por FUERZA BRUTA (los 2^n subconjuntos).
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from .instance import MKPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def _total(inst, sol) -> float:
    """Costo de una selección plana."""
    return sum(ref.cost_terms(inst, ref.wrap(sol)).values())


def _feasible(inst, sol) -> bool:
    return not any(ref.violations(inst, ref.wrap(sol)).values())


def brute_force_optimum(inst: MKPInstance) -> tuple[float, list[int]]:
    best, best_sol = float("inf"), None
    for sol in itertools.product((0, 1), repeat=inst.n_items):
        if _feasible(inst, sol):
            c = _total(inst, sol)
            if c < best:
                best, best_sol = c, list(sol)
    return best, best_sol


def build_cases(sizes=((6, 2), (7, 2), (8, 3), (8, 2), (10, 3), (10, 5)), seed: int = 2026) -> list[dict]:
    out = []
    for k, (n, m) in enumerate(sizes):
        inst = MKPInstance.random(n, m, Random(seed + k), tightness=[0.25, 0.5][k % 2])
        opt, opt_sol = brute_force_optimum(inst)
        triv = list(ref.trivial_solution(inst)[0])
        # un solo ítem que no esté en la óptima, agregado a ella: infactible por capacidad (si no, es mejor que la óptima)
        extra = next(j for j in inst.items if not opt_sol[j])
        over = [1 if j == extra else x for j, x in enumerate(opt_sol)]
        sols = [
            {"answer": [triv], "feasible": True, "cost": round(_total(inst, triv), 6)},
            {"answer": [opt_sol], "feasible": True, "cost": round(opt, 6)},
            {"answer": [[0] * n], "feasible": True, "cost": 0.0},
            {"answer": [[1] * n], "feasible": False, "violates": ["capacidad"]},
            {"answer": [over], "feasible": False, "violates": ["capacidad"]},
        ]
        out.append({"name": f"mkp_{k}_{n}x{m}", "instance": inst.to_text(), "optimum": round(opt, 6),
                    "solutions": sols, "visible": k == 0})
    return out


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], MKPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"),
                     c.get("visible", False), c["instance"]) for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    print(f"{len(cases)} casos en {CASES_PATH}")


if __name__ == "__main__":
    main()
