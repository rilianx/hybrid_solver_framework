"""Casos de prueba del SSCFLP al estilo Codeforces (`cases.json`): micro-instancias con respuestas conocidas, para validar
un modelo generado (`core.validation.model_parts`).

    python -m examples.sscflp.cases        # regenera cases.json

Cada caso trae la instancia en el formato de entrada (`SSCFLPInstance.to_text`), soluciones en el formato neutral (el
centro de cada cliente, en una lista de una lista) con su factibilidad, la familia violada o el costo, y el óptimo por
FUERZA BRUTA (las n^m asignaciones). Las instancias tienen poca holgura de capacidad (1.3 veces la demanda) para que la capacidad decida.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from .instance import SSCFLPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def _total(inst, sol) -> float:
    """Costo de una asignación plana."""
    return sum(ref.cost_terms(inst, ref.wrap(sol)).values())


def _feasible_assignments(inst: SSCFLPInstance):
    for sol in itertools.product(inst.facilities, repeat=inst.n_customers):
        if not any(ref.violations(inst, ref.wrap(sol)).values()):
            yield list(sol)


def brute_force_optimum(inst: SSCFLPInstance) -> tuple[float, list[int]]:
    best, best_sol = float("inf"), None
    for sol in _feasible_assignments(inst):
        c = _total(inst, sol)
        if c < best:
            best, best_sol = c, list(sol)
    return best, best_sol


def micro_instance(n: int, m: int, seed: int) -> SSCFLPInstance:
    """Una micro-instancia con la trivial factible y en la que un solo centro no alcanza (la capacidad importa)."""
    rng = Random(seed)
    while True:
        inst = SSCFLPInstance.random(n, m, rng, ratio=1.3)
        try:
            ref.trivial_solution(inst)
        except ValueError:
            continue
        if sum(inst.demand) > max(inst.capacity):
            return inst


def build_cases(sizes=((3, 5), (3, 6), (4, 6), (3, 7), (4, 7), (4, 7)), seed: int = 2026) -> list[dict]:
    out = []
    for k, (n, m) in enumerate(sizes):
        inst = micro_instance(n, m, seed + k)
        opt, opt_sol = brute_force_optimum(inst)
        triv = list(ref.trivial_solution(inst)[0])
        big = max(inst.facilities, key=lambda i: (inst.capacity[i], -i))
        unserved = triv[:-1] + [-1]  # el último cliente sin atender
        sols = [
            {"answer": [triv], "feasible": True, "cost": round(_total(inst, triv), 6)},
            {"answer": [opt_sol], "feasible": True, "cost": round(opt, 6)},
            {"answer": [[big] * m], "feasible": False, "violates": ["capacidad"]},  # todos al centro más grande
            {"answer": [unserved], "feasible": False, "violates": ["asignacion"]},
        ]
        # la factible más cara (abre muchos centros: prueba los costos fijos de los abiertos)
        worst = max(_feasible_assignments(inst), key=lambda s: (_total(inst, s), s))
        sols.insert(2, {"answer": [worst], "feasible": True, "cost": round(_total(inst, worst), 6)})
        out.append({"name": f"sscflp_{k}_{n}x{m}", "instance": inst.to_text(), "optimum": round(opt, 6),
                    "solutions": sols, "visible": k == 0})
    return out


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], SSCFLPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"),
                     c.get("visible", False), c["instance"]) for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    print(f"{len(cases)} casos en {CASES_PATH}")


if __name__ == "__main__":
    main()
