"""Casos de prueba del CLSP al estilo Codeforces (`cases.json`): micro-instancias con respuestas
conocidas, para validar un `ProblemModel` generado (`core.validation.model_parts`).

    python -m examples.lotsizing.cases        # regenera cases.json

Cada caso trae la instancia en el formato de entrada (`CLSPInstance.to_text`), planes de setups
en el formato neutral (matriz 0/1 ítem × período) con su factibilidad, la familia violada o el
costo, y el óptimo calculado por FUERZA BRUTA (todos los planes de setups, cada uno con su LP de
producción), contrastado con el MIP escrito a mano (`problem_model.CLSPMip`).
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from .instance import CLSPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def brute_force_optimum(inst: CLSPInstance) -> tuple[float, tuple]:
    best, best_sol = float("inf"), None
    I, T = inst.n_items, inst.n_periods
    for bits in itertools.product((False, True), repeat=I * T):
        sol = tuple(tuple(bits[i * T:(i + 1) * T]) for i in range(I))
        if ref.violations(inst, sol)["demanda"] > 1e-6:
            continue
        cost = sum(ref.cost_terms(inst, sol).values())
        if cost < best - 1e-9:
            best, best_sol = cost, sol
    return best, best_sol


def handwritten_optimum(inst: CLSPInstance) -> float:
    from .problem_model import CLSPMip

    mip = CLSPMip(inst)
    mip.solve(fixed={}, integer=set(mip.variables()), relaxed=set(), time_limit=60)
    return mip.last_objective


def _answer(sol) -> list[list[int]]:
    return [[int(v) for v in row] for row in sol]


def _labelled(inst: CLSPInstance, sol) -> dict:
    short = ref.violations(inst, sol)["demanda"]
    if short > 1e-6:
        return {"answer": _answer(sol), "feasible": False, "violates": ["demanda"]}
    return {"answer": _answer(sol), "feasible": True, "cost": round(sum(ref.cost_terms(inst, sol).values()), 6)}


def build_cases(sizes=((2, 3), (2, 4), (3, 3), (3, 4), (3, 4), (4, 3)), seed: int = 2026) -> list[dict]:
    out = []
    for k, (n, T) in enumerate(sizes):
        inst = CLSPInstance.trigeiro(n, T, Random(seed + k), utilization=0.9, tbo=3.0)
        opt, opt_sol = brute_force_optimum(inst)
        hw = handwritten_optimum(inst)
        assert abs(opt - hw) <= 1e-4 * max(1.0, abs(opt)), (k, opt, hw)
        lfl = tuple(tuple(d > 0 for d in row) for row in inst.demand)  # setup donde hay demanda
        first = tuple(tuple(t == 0 for t in range(T)) for _ in range(n))  # todo en el primer período
        off = tuple(tuple(False for _ in range(T)) for _ in range(n))
        sols = [_labelled(inst, ref.trivial_solution(inst)), _labelled(inst, lfl), _labelled(inst, opt_sol),
                _labelled(inst, first), _labelled(inst, ref.random_solution(inst, Random(k)))]
        if any(sum(row) > 0 for row in inst.demand):
            sols.append(_labelled(inst, off))
        out.append({"name": f"clsp_{k}_{n}x{T}", "instance": inst.to_text(), "optimum": round(opt, 6),
                    "solutions": sols, "visible": k == 0})
    return out


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], CLSPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"), c.get("visible", False),
                     c["instance"]) for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    feas = sum(s["feasible"] for c in cases for s in c["solutions"])
    print(f"{len(cases)} casos en {CASES_PATH}: {feas} respuestas factibles, "
          f"{sum(len(c['solutions']) for c in cases) - feas} infactibles")


if __name__ == "__main__":
    main()
