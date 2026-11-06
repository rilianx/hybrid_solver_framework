"""Referencias para los test de ReEvo (= los MKP100…1000 de MCTS-AHD): CBC con límite de tiempo.

    python -m examples.mkp.fetch --reevo
    python -m examples.mkp.reference --sizes 100 200 --seconds 60 --workers 4

Guarda `examples/mkp/reevo_best_known.json` (en el repositorio; las instancias no, se reproducen con `fetch --reevo`):
{instancia: {"ub": costo = -beneficio de la mejor solución, "opt": CBC probó optimalidad, "source"}}. Sin optimalidad
probada es una mejor conocida, no un óptimo.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from . import model_parts as ref
from .instance import MKPInstance

HERE = Path(__file__).parent
OUT = HERE / "reevo_best_known.json"


def solve_cbc(inst: MKPInstance, seconds: float) -> tuple[list[int], bool]:
    import pulp

    prob = pulp.LpProblem("mkp", pulp.LpMaximize)
    x = [pulp.LpVariable(f"x{j}", cat="Binary") for j in inst.items]
    prob += pulp.lpSum(inst.profit[j] * x[j] for j in inst.items)
    for i in inst.resources:
        prob += pulp.lpSum(inst.weight[i][j] * x[j] for j in inst.items) <= inst.capacity[i]
    t0 = time.time()
    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=seconds, gapRel=0.0, gapAbs=0.0))
    sol = [int(round(v.value() or 0.0)) for v in x]
    opt = pulp.LpStatus[prob.status] == "Optimal" and time.time() - t0 < seconds * 0.98
    return sol, opt


def _job(args):
    path, seconds = args
    inst = MKPInstance.load(str(path))
    sol, opt = solve_cbc(inst, seconds)
    sol = ref.canonical(sol)
    assert not any(ref.violations(inst, sol).values()), path
    # la greedy como respaldo si CBC no llegó a algo mejor en el tiempo
    triv = ref.trivial_solution(inst)
    cost = sum(ref.cost_terms(inst, sol).values())
    if sum(ref.cost_terms(inst, triv).values()) < cost:
        sol, cost, opt = triv, sum(ref.cost_terms(inst, triv).values()), False
    return path.stem, {"ub": round(cost, 9), "opt": opt, "source": f"CBC {seconds:g} s"}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sizes", nargs="*", type=int, default=[100, 200])
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [p for n in args.sizes for p in sorted((HERE / "reevo").glob(f"test{n}_*.txt")) if p.stem not in out]
    with ProcessPoolExecutor(args.workers) as ex:
        for name, res in ex.map(_job, [(p, args.seconds) for p in todo]):
            out[name] = res
            OUT.write_text(json.dumps(dict(sorted(out.items(), key=lambda kv: (len(kv[0]), kv[0]))), indent=1) + "\n")
            print(name, res, flush=True)


if __name__ == "__main__":
    main()
