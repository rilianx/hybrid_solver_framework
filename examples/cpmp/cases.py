"""Casos de prueba del CPMP al estilo Codeforces (`cases.json`): micro-instancias con respuestas
conocidas, para validar un `ProblemModel` generado (`core.validation.model_parts`).

    python -m examples.cpmp.cases        # regenera cases.json

Cada caso trae la instancia en el formato de los benchmarks ("Tiers: H", "Stack i: g g g"),
soluciones en el formato neutral (lista de [so, sd]) con su factibilidad, la familia violada o
el costo, y el óptimo EXACTO calculado por búsqueda en anchura sobre los layouts. En un problema
nuevo, estos casos los escribe quien plantea el problema; aquí se generan para tener un banco
de prueba del mecanismo.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from random import Random

from core.model_parts import TestCase

from . import model_parts as ref
from .instance import CPMPInstance

CASES_PATH = Path(__file__).with_name("cases.json")


def bfs_optimum(inst: CPMPInstance) -> list[tuple[int, int]]:
    start = tuple(tuple(s) for s in inst.stacks)
    parent = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        if ref._bad(state) == 0:
            path = []
            while parent[state] is not None:
                state, m = parent[state]
                path.append(m)
            return path[::-1]
        for so, src in enumerate(state):
            if not src:
                continue
            for sd, dst in enumerate(state):
                if sd == so or len(dst) >= inst.H:
                    continue
                nxt = list(state)
                nxt[so], nxt[sd] = src[:-1], dst + (src[-1],)
                nxt = tuple(nxt)
                if nxt not in parent:
                    parent[nxt] = (state, (so, sd))
                    queue.append(nxt)
    raise ValueError("instancia sin solución")


def to_text(inst: CPMPInstance) -> str:
    lines = [f"Tiers: {inst.H}", f"Stacks: {inst.S}", f"Containers: {inst.N}"]
    lines += [f"Stack {i + 1}: {' '.join(map(str, s))}" for i, s in enumerate(inst.stacks)]
    return "\n".join(lines) + "\n"


def build_cases(sizes=((3, 4), (4, 4), (4, 4), (5, 4), (5, 4), (4, 5)), seed: int = 2026) -> list[dict]:
    """Al estilo CVS (grupos distintos, pilas de altura H − 2), salvo el último: al estilo BF,
    con grupos repetidos y pilas de alturas distintas."""
    out = []
    for k, (S, H) in enumerate(sizes):
        last = k == len(sizes) - 1
        for attempt in range(100):  # instancias con al menos 3 movimientos óptimos
            rng = Random(seed + 100 * k + attempt)
            inst = CPMPInstance.bf_like(S, H, rng, fill=0.5, group_ratio=0.5) if last else CPMPInstance.cvs_like(S, H, rng)
            opt = bfs_optimum(inst)
            if len(opt) >= 3:
                break
        triv = ref.trivial_solution(inst)
        so = next(i for i in range(inst.S) if inst.stacks[i])
        sd = next(i for i in range(inst.S) if i != so and len(inst.stacks[i]) < inst.H)
        detour = [[so, sd], [sd, so]] + [list(m) for m in opt]  # ida y vuelta: factible, 2 movimientos más
        sols = [
            {"answer": [list(m) for m in opt], "feasible": True, "cost": float(len(opt))},
            {"answer": [list(m) for m in triv], "feasible": True, "cost": float(len(triv))},
            {"answer": detour, "feasible": True, "cost": float(len(detour))},
        ]
        if opt:
            sols.append({"answer": [list(m) for m in opt[:-1]], "feasible": False, "violates": ["orden"]})
            empty = next(i for i in range(inst.S) if not inst.stacks[i]) if any(not s for s in inst.stacks) else None
            bad_move = [[empty, (empty + 1) % inst.S]] if empty is not None else [[0, 0]]
            sols.append({"answer": bad_move + [list(m) for m in opt], "feasible": False, "violates": ["movimiento"]})
        out.append({"name": f"cpmp_{k}_{S}x{H}", "instance": to_text(inst), "optimum": float(len(opt)),
                    "solutions": sols, "visible": k == 0})
    return out


def load_cases(path: str | Path = CASES_PATH) -> list[TestCase]:
    data = json.loads(Path(path).read_text())
    return [TestCase(c["name"], CPMPInstance.parse(c["instance"]), c["solutions"], c.get("optimum"), c.get("visible", False),
                     c["instance"]) for c in data]


def main() -> None:
    cases = build_cases()
    CASES_PATH.write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    print(f"{len(cases)} casos en {CASES_PATH}")


if __name__ == "__main__":
    main()
