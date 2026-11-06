"""Las referencias del benchmark del SSCFLP (`bench/best_known.json`): el óptimo o la mejor solución conocida de cada
instancia, y la mejor cota inferior cuando no hay óptimo probado.

    python -m examples.sscflp.best_known --cbc H- D- --time 600 --workers 4   # óptimos con CBC (formulación fuerte)
    python -m examples.sscflp.best_known --literature                              # Yang, TB4 e i1000 (Kong 2021)

Formulación: x_ij binaria (cliente j atendido por i), y_i binaria (centro i abierto); min Σ f_i y_i + Σ c_ij x_ij;
Σ_i x_ij = 1; Σ_j d_j x_ij <= s_i y_i; y además x_ij <= y_i (la desigualdad fuerte que hace chica la brecha de la
relajación). Cada entrada es {"ub": costo, "lb": cota, "opt": bool, "source": ...}.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .instance import SSCFLPInstance

BENCH = Path(__file__).with_name("bench")
PATH = BENCH / "best_known.json"

# Kong (2021), "A matheuristic algorithm for the single-source capacitated facility location problem and its variants",
# arXiv:2112.12974, tablas 1–6 del apéndice (óptimos de la literatura y de CPLEX 12.6, mejores conocidas y cotas).
# TB4: (lb, ub) cuando el óptimo no está probado; i1000: (lb, mejor conocida).
LIT_YANG = {
    "30_200_1": 30181, "30_200_2": 28923, "30_200_3": 28131, "30_200_4": 28152, "30_200_5": 27646,
    "60_200_1": 27977, "60_200_2": 29704, "60_200_3": 27993, "60_200_4": 27691, "60_200_5": 29195,
    "60_300_1": 35648, "60_300_2": 35474, "60_300_3": 33872, "60_300_4": 33096, "60_300_5": 30918,
    "80_400_1": 39318, "80_400_2": 37076, "80_400_3": 43859, "80_400_4": 37344, "80_400_5": 43508,
}
LIT_TB4 = {
    "50_100_2_1": 18294, "50_100_2_2": 19688, "50_100_2_3": 19075, "50_100_2_4": 18620, "50_100_2_5": 18502,
    "50_100_3_1": 16948, "50_100_3_2": 15063, "50_100_3_3": 15107, "50_100_3_4": 14347, "50_100_3_5": 14813,
    "50_100_5_1": 12072, "50_100_5_2": 11898, "50_100_5_3": 11125, "50_100_5_4": 11817, "50_100_5_5": 11489,
    "50_200_2_1": 25992, "50_200_2_2": 25868, "50_200_2_3": 26930, "50_200_2_4": (25951.63, 25954),
    "50_200_2_5": (25326.50, 25329),
    "50_200_3_1": 20701, "50_200_3_2": 22021, "50_200_3_3": 20038, "50_200_3_4": 20595, "50_200_3_5": 21168,
    "50_200_5_1": 16659, "50_200_5_2": 16138, "50_200_5_3": 17755, "50_200_5_4": 15858, "50_200_5_5": 16884,
    "60_300_2_1": (34858.5, 34860), "60_300_2_2": (36543.5, 36551), "60_300_2_3": (34876.2, 34878),
    "60_300_2_4": (34817.6, 34821), "60_300_2_5": (37138.1, 37142),
    "60_300_3_1": 27903, "60_300_3_2": 27594, "60_300_3_3": 29231, "60_300_3_4": 27439, "60_300_3_5": 28033,
    "60_300_5_1": 21045, "60_300_5_2": 22589, "60_300_5_3": 21449, "60_300_5_4": 21466, "60_300_5_5": 21860,
}
LIT_I1000 = {
    "i1000_1": (49681.02, 50037), "i1000_2": (50842.16, 51277.80), "i1000_3": (47362.62, 47737.73),
    "i1000_4": (49029.12, 49408.86), "i1000_5": (50971.44, 51415.41), "i1000_6": (27823.84, 28043.73),
    "i1000_7": (27252.32, 27412.21), "i1000_8": (27375.37, 27543.01), "i1000_9": (26857.09, 26992.81),
    "i1000_10": (27186.99, 27397.38), "i1000_11": (22180.33, 22247.61), "i1000_12": (22160.39, 22227),
    "i1000_13": (22657.09, 22745.61), "i1000_14": (22312.01, 22405.92), "i1000_15": (22629.44, 22704),
    "i1000_16": (21331.81, 21390.24), "i1000_17": (21209.83, 21234.62), "i1000_18": (20739.20, 20753.39),
    "i1000_19": (20537.45, 20597.01), "i1000_20": (21560.86, 21601),
}
KONG = "Kong (2021), arXiv:2112.12974"


def literature() -> dict[str, dict]:
    out = {}
    for table, prefix, src in ((LIT_YANG, "Y-", KONG), (LIT_TB4, "TB4-", KONG),
                               (LIT_I1000, "", KONG + " y github.com/yfkong/Unified")):
        for k, v in table.items():
            lb, ub = v if isinstance(v, tuple) else (v, v)
            out[prefix + k] = {"ub": ub, "lb": lb, "opt": lb == ub, "source": src}
    return out


def solve_cbc(path: str, seconds: float) -> dict:
    import pulp

    from . import model_parts as ref

    inst = SSCFLPInstance.load(path)
    I, J = inst.facilities, inst.customers
    prob = pulp.LpProblem("sscflp", pulp.LpMinimize)
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", cat="Binary") for i in I for j in J}
    y = {i: pulp.LpVariable(f"y_{i}", cat="Binary") for i in I}
    prob += pulp.lpSum(inst.fixed[i] * y[i] for i in I) + pulp.lpSum(inst.cost[i][j] * x[i, j] for i in I for j in J)
    for j in J:
        prob += pulp.lpSum(x[i, j] for i in I) == 1
    for i in I:
        prob += pulp.lpSum(inst.demand[j] * x[i, j] for j in J) <= inst.capacity[i] * y[i]
        for j in J:
            prob += x[i, j] <= y[i]
    t0 = time.time()
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=seconds, gapRel=0.0, gapAbs=0.0)
    prob.solve(solver)
    sol = [max(I, key=lambda i: x[i, j].value() or 0.0) for j in J]
    v = ref.violations(inst, sol)
    assert not any(val > 1e-6 for val in v.values()), (path, v)
    ub = sum(ref.cost_terms(inst, sol).values())
    status = pulp.LpStatus[prob.status]
    opt = status == "Optimal" and time.time() - t0 < seconds * 0.98
    # sin óptimo probado no hay cota: CBC por línea de comandos no la informa
    return {"ub": round(ub, 6), "lb": round(ub, 6) if opt else None, "opt": opt,
            "source": f"CBC {seconds:g} s" + ("" if opt else " (sin probar optimalidad)"),
            "time": round(time.time() - t0, 1), "solution": sol}


def _job(args):
    name, seconds = args
    return name, solve_cbc(str(BENCH / f"{name}.txt"), seconds)


def load() -> dict[str, dict]:
    return {k: v for k, v in json.loads(PATH.read_text()).items() if not k.startswith("_")} if PATH.exists() else {}


def save(entries: dict[str, dict]) -> None:
    def key(k):
        import re
        return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", k)]

    data = {"_fuente": "examples/sscflp/best_known.py: CBC con la formulación fuerte (H-, D-) y Kong (2021), "
                       "arXiv:2112.12974 (Y-, TB4-, i1000_). ub = mejor solución conocida, lb = mejor cota inferior, "
                       "opt = ub probado óptimo."}
    data.update({k: entries[k] for k in sorted(entries, key=key)})
    PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cbc", nargs="*", default=None, help="prefijos de las instancias a resolver con CBC")
    ap.add_argument("--literature", action="store_true")
    ap.add_argument("--time", type=float, default=600)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--redo", action="store_true", help="volver a resolver las que ya tienen óptimo")
    args = ap.parse_args(argv)
    entries = load()
    if args.literature:
        entries.update(literature())
        save(entries)
    if args.cbc is not None:
        names = sorted(p.stem for p in BENCH.glob("*.txt") if any(p.stem.startswith(q) for q in args.cbc))
        names = [n for n in names if args.redo or not entries.get(n, {}).get("opt")]
        with ProcessPoolExecutor(args.workers) as ex:
            for name, res in ex.map(_job, [(n, args.time) for n in names]):
                res.pop("solution")
                entries[name] = res
                save(entries)
                print(name, res, flush=True)


if __name__ == "__main__":
    main()
