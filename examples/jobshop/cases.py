"""Casos de prueba del job shop al estilo Codeforces (`cases.json`): micro-instancias con respuestas
conocidas, para validar un modelo generado (`core.validation.model_parts`).

    python -m examples.jobshop.cases        # regenera cases.json

Cada caso trae la instancia en el formato de entrada (`JSSPInstance.to_text`), soluciones en el
formato neutral (una secuencia de trabajos por máquina) con su factibilidad, la familia violada o el
makespan, y el óptimo calculado por FUERZA BRUTA (todas las combinaciones de permutaciones por
máquina), contrastado con el MIP de referencia.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from .instance import JSSPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def brute_force_optimum(inst: JSSPInstance) -> tuple[float, list[list[int]]]:
    best, best_sol = float("inf"), None
    perms = [list(itertools.permutations(ref.jobs_on(inst, m))) for m in inst.machines]
    for combo in itertools.product(*perms):
        _, mk, released = ref.schedule(inst, combo)
        if not released and mk < best:
            best, best_sol = mk, [list(s) for s in combo]
    return float(best), best_sol


def _earliest_end(inst: JSSPInstance):
    p = ref.empty_partial(inst)
    while not ref.is_complete(inst, p):
        p = ref.apply_action(inst, p, min(ref.candidates(inst, p), key=lambda a: (a.end, a.job)))
    return ref.to_solution(inst, p)


def _cyclic(inst: JSSPInstance, rng: Random):
    """Secuencias válidas (permutaciones) que forman un ciclo con las rutas."""
    while True:
        sol = tuple(tuple(rng.sample(ref.jobs_on(inst, m), len(ref.jobs_on(inst, m)))) for m in inst.machines)
        if ref.schedule(inst, sol)[2]:
            return [list(s) for s in sol]


def _answer(sol) -> list[list[int]]:
    return [list(s) for s in sol]


def _cost(inst, sol) -> float:
    return round(ref.cost_terms(inst, ref.canonical(sol))["makespan"], 6)


def build_cases(sizes=((3, 3), (3, 3), (4, 3), (3, 4), (4, 3), (4, 4)), seed: int = 2026) -> list[dict]:
    out = []
    for k, (n, m) in enumerate(sizes):
        rng = Random(seed + k)
        inst = JSSPInstance.random(n, m, rng)
        opt, opt_sol = brute_force_optimum(inst)
        triv = ref.trivial_solution(inst)
        greedy = _earliest_end(inst)
        rand = ref.random_solution(inst, Random(seed + 100 + k))
        missing = _answer(triv)
        missing[0] = missing[0][1:]  # la máquina 0 no procesa al primer trabajo
        sols = [
            {"answer": _answer(triv), "feasible": True, "cost": _cost(inst, triv)},
            {"answer": _answer(greedy), "feasible": True, "cost": _cost(inst, greedy)},
            {"answer": _answer(rand), "feasible": True, "cost": _cost(inst, rand)},
            {"answer": opt_sol, "feasible": True, "cost": round(opt, 6)},
            {"answer": missing, "feasible": False, "violates": ["secuencia"]},
            {"answer": _cyclic(inst, rng), "feasible": False, "violates": ["orden"]},
        ]
        out.append({"name": f"jobshop_{k}_{n}x{m}", "instance": inst.to_text(), "optimum": round(opt, 6),
                    "solutions": sols, "visible": k == 0})
    return out


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], JSSPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"), c.get("visible", False),
                     c["instance"]) for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    print(f"{len(cases)} casos en {CASES_PATH}")


if __name__ == "__main__":
    main()
