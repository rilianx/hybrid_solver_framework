"""Casos de prueba del PFSP con makespan (`cases.json`), al estilo Codeforces: micro-instancias con el óptimo por
fuerza bruta y respuestas con su factibilidad, la familia violada o el costo.

    python -m examples.flowshop_cmax.cases        # regenera cases.json
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from examples.flowshop.instance import PFSPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def _answer(inst, ans) -> dict:
    sol = ref.from_answer(inst, ans)
    v = {k: x for k, x in ref.violations(inst, sol).items() if x > 1e-9}
    out = {"answer": ans, "feasible": not v}
    if v:
        out["violates"] = sorted(v)
    else:
        out["cost"] = sum(ref.cost_terms(inst, sol).values())
    return out


def build_cases() -> list[dict]:
    cases = []
    for k, (n, m) in enumerate([(3, 2), (4, 3), (5, 2), (5, 4), (6, 3), (6, 5), (7, 3), (7, 4)]):
        rng = Random(1000 + k)
        inst = PFSPInstance.random(n, m, rng)
        best, best_perm = float("inf"), None
        for perm in itertools.permutations(range(n)):
            c = ref.cost_terms(inst, (perm,))["makespan"]
            if c < best:
                best, best_perm = c, perm
        perms = [list(best_perm), list(range(n))] + [rng.sample(range(n), n) for _ in range(2)]
        wrong = [list(range(n - 1)), list(range(n)) + [0], [0] + list(range(n - 1)), list(range(n - 1)) + [n]]
        cases.append({"name": f"pfspc_{k}_{n}x{m}", "instance": inst.to_text(), "optimum": best, "visible": k < 3,
                      "solutions": [_answer(inst, [p]) for p in perms + wrong]})
    return cases


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], PFSPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"), c.get("visible", False),
                     c["instance"]) for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1))
    print(f"{len(cases)} casos en {CASES_PATH}")


if __name__ == "__main__":
    main()
