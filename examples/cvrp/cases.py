"""Casos de prueba del CVRP al estilo Codeforces (`cases.json`): micro-instancias con respuestas
conocidas, para validar un `ProblemModel` generado (`core.validation.model_parts`).

    python -m examples.cvrp.cases        # regenera cases.json

Cada caso trae la instancia en el formato de entrada (`CVRPInstance.to_text`), soluciones en el
formato neutral (lista de rutas) con su factibilidad, la familia violada o el costo, y el óptimo
calculado por FUERZA BRUTA (todas las particiones de los clientes en rutas, todos los órdenes),
contrastado con el MIP de referencia. En un problema nuevo, estos casos los escribe quien plantea
el problema; aquí se generan para tener un banco de prueba del mecanismo.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from .instance import CVRPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def _partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in _partitions(rest):
        for k in range(len(part)):
            yield part[:k] + [[first] + part[k]] + part[k + 1:]
        yield [[first]] + part


def brute_force_optimum(inst: CVRPInstance) -> tuple[float, list[list[int]]]:
    best, best_sol = float("inf"), None
    for part in _partitions(list(inst.customers)):
        if any(sum(inst.demand[c] for c in block) > inst.capacity for block in part):
            continue
        total, routes = 0.0, []
        for block in part:  # mejor orden de cada ruta, por separado
            b_cost, b_route = min((ref.cost_terms(inst, (perm,))["distancia"], perm) for perm in itertools.permutations(block))
            total += b_cost
            routes.append(list(b_route))
        if total < best:
            best, best_sol = total, routes
    return best, best_sol


def _answer(sol) -> list[list[int]]:
    return [list(r) for r in sol]


def build_cases(sizes=(4, 5, 5, 6, 6, 6), seed: int = 2026) -> list[dict]:
    from core.construction import GreedyConstructor

    from .construction import CheapestInsertion
    from .problem_model import CVRPModel

    out = []
    for k, n in enumerate(sizes):
        inst = CVRPInstance.random(n, Random(seed + k), route_size=2.5, clustered=k % 2 == 1)
        P = CVRPModel(inst)
        opt, opt_routes = brute_force_optimum(inst)
        triv = ref.trivial_solution(inst)
        greedy = GreedyConstructor(P, CheapestInsertion(P)).build(inst, Random(0))
        custs = list(inst.customers)
        sols = [
            {"answer": _answer(triv), "feasible": True, "cost": round(ref.cost_terms(inst, triv)["distancia"], 6)},
            {"answer": _answer(greedy), "feasible": True, "cost": round(ref.cost_terms(inst, greedy)["distancia"], 6)},
            {"answer": opt_routes, "feasible": True, "cost": round(opt, 6)},
            {"answer": [custs[1:]], "feasible": False, "violates": ["visita"]},  # falta el cliente 1
            {"answer": [custs, [custs[0]]], "feasible": False, "violates": ["visita"]},  # cliente 1 repetido
        ]
        if sum(inst.demand[c] for c in custs) > inst.capacity:
            sols.append({"answer": [custs], "feasible": False, "violates": ["capacidad"]})
        out.append({"name": f"cvrp_{k}_{n}c", "instance": inst.to_text(), "optimum": round(opt, 6),
                    "solutions": sols, "visible": k == 0})
    return out


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], CVRPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"), c.get("visible", False))
            for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    print(f"{len(cases)} casos en {CASES_PATH}")


if __name__ == "__main__":
    main()
