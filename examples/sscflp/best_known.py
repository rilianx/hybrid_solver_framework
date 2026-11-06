"""Las referencias del benchmark del SSCFLP (`bench/best_known.json`): la mejor solución conocida de cada instancia (`ub`),
la mejor cota inferior (`lb`) y si `ub` está probado óptimo (`opt`).

    python -m examples.sscflp.best_known --literature          # Guastaroba y Speranza (2014) y Kong (2021)
    python -m examples.sscflp.best_known --cbc D- --time 600   # óptimos con CBC (Díaz-Fernández no tiene tabla)

Fuentes, combinadas por instancia (lb = la mayor, ub = la menor):
- Guastaroba y Speranza (2014), EJOR 238(2): los valores de OR-Brescia (`bench/refs/*_Solution_Values.txt`): óptimos
  de Holmberg, Yang y la OR-Library; cota u óptimo (*) y mejor solución de TBED1.
- Kong (2021), arXiv:2112.12974, tablas del apéndice: TB4 (óptimos o cota y mejor conocida, con las correcciones de su
  tabla 4), los óptimos nuevos de TBED1 (tabla 5) y sus cotas y mejores soluciones de TBED1 (tabla 3); y sus mejores soluciones de TBED1
  (github.com/yfkong/Unified, `bench/refs/kong2021_tbed1_solutions.json`), cuyo costo se evalúa con el oráculo.
- CBC con la formulación fuerte: x_ij binaria (cliente j atendido por i), y_i binaria (centro i abierto);
  min Σ f_i y_i + Σ c_ij x_ij; Σ_i x_ij = 1; Σ_j d_j x_ij <= s_i y_i; x_ij <= y_i.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .instance import SSCFLPInstance

BENCH = Path(__file__).with_name("bench")
REFS = BENCH / "refs"
PATH = BENCH / "best_known.json"
GS = "Guastaroba y Speranza (2014)"
KONG = "Kong (2021)"

# Kong (2021), tabla 2 (TB4): el óptimo, o (lb, ub) cuando no está probado (ub de sus tablas 4 y 6)
KONG_TB4 = {
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
# Kong (2021), tabla 5: óptimos nuevos de TBED1 (CPLEX 12.6)
KONG_TBED1_OPT = {"i300_6": 11326.43, "i300_7": 11470.31, "i500_6": 15853.35, "i500_7": 16205.15, "i500_9": 16399.40,
                  "i500_10": 15886.54, "i500_13": 13715.96, "i500_15": 13947.12, "i700_14": 17383.87,
                  "i700_20": 15492.02}
# Kong (2021), tabla 3: (cota inferior, columna NewLB; mejor solución de su matheurística, columna Objmin) de TBED1
KONG_TBED1 = {
    "i300_1": (16555.77, 16563.14), "i300_2": (16059.34, 16135.82), "i300_3": (15606.10, 15666.23),
    "i300_4": (18143.89, 18255.10), "i300_5": (18191.11, 18291.05), "i300_6": (11326.43, 11329.93),
    "i300_7": (11470.31, 11473.11), "i300_8": (11449.67, 11455.19), "i300_9": (10932.88, 10932.88),
    "i300_10": (11324.34, 11324.34), "i300_11": (10046.94, 10050.50), "i300_12": (9359.64, 9359.64),
    "i300_13": (10103.49, 10103.49), "i300_14": (9738.05, 9738.05), "i300_15": (9902.26, 9902.26),
    "i300_16": (9168.08, 9168.08), "i300_17": (9181.07, 9181.07), "i300_18": (9581.95, 9581.95),
    "i300_19": (9062.16, 9062.16), "i300_20": (9077.85, 9077.85), "i500_1": (26566.69, 26731.63),
    "i500_2": (28268.41, 28460.43), "i500_3": (28067.69, 28284.36), "i500_4": (28268.36, 28489.69),
    "i500_5": (24805.56, 24995.73), "i500_6": (15853.35, 15867.59), "i500_7": (16205.15, 16205.15),
    "i500_8": (16081.54, 16125.30), "i500_9": (16399.40, 16430.98), "i500_10": (15857.97, 15887.80),
    "i500_11": (13497.71, 13504.94), "i500_12": (14736.38, 14736.38), "i500_13": (13715.96, 13715.96),
    "i500_14": (13629.54, 13634.91), "i500_15": (13947.12, 13947.38), "i500_16": (12618.68, 12618.68),
    "i500_17": (13386.17, 13386.17), "i500_18": (12852.52, 12852.52), "i500_19": (13521.52, 13521.59),
    "i500_20": (12362.20, 12362.20), "i700_1": (37054.60, 37343.34), "i700_2": (34488.56, 34817.44),
    "i700_3": (34485.24, 34759.07), "i700_4": (38260.98, 38534.35), "i700_5": (37950.49, 38230.13),
    "i700_6": (19910.67, 20065.19), "i700_7": (21297.30, 21433.56), "i700_8": (20702.95, 20820.70),
    "i700_9": (20979.88, 21104.52), "i700_10": (22055.41, 22210.50), "i700_11": (17120.15, 17188.47),
    "i700_12": (18135.97, 18201.06), "i700_13": (17277.92, 17299.20), "i700_14": (17383.87, 17383.87),
    "i700_15": (18167.98, 18220.75), "i700_16": (16029.55, 16029.55), "i700_17": (16199.55, 16199.55),
    "i700_18": (16443.07, 16443.07), "i700_19": (16399.79, 16407.94), "i700_20": (15492.02, 15492.02),
    "i1000_1": (49681.02, 50104.98), "i1000_2": (50842.16, 51277.80), "i1000_3": (47362.62, 47737.73),
    "i1000_4": (49029.12, 49408.86), "i1000_5": (50971.44, 51415.41), "i1000_6": (27823.84, 28043.73),
    "i1000_7": (27252.32, 27412.21), "i1000_8": (27375.37, 27543.01), "i1000_9": (26857.09, 26992.81),
    "i1000_10": (27186.99, 27397.38), "i1000_11": (22180.33, 22247.61), "i1000_12": (22160.39, 22231.18),
    "i1000_13": (22657.09, 22745.61), "i1000_14": (22312.01, 22405.92), "i1000_15": (22629.44, 22704.67),
    "i1000_16": (21331.81, 21390.24), "i1000_17": (21209.83, 21234.62), "i1000_18": (20739.20, 20753.39),
    "i1000_19": (20537.45, 20597.01), "i1000_20": (21560.86, 21601.55), "i3001500_1": (154999.14, 154999.19),
    "i3001500_2": (159438.03, 159446.39), "i3001500_3": (157300.15, 157306.78), "i3001500_4": (157796.28, 157797.17),
    "i3001500_5": (161305.97, 161305.97), "i3001500_6": (156667.31, 156667.31), "i3001500_7": (157031.55, 157031.55),
    "i3001500_8": (157796.21, 157796.21), "i3001500_9": (156968.46, 156968.46), "i3001500_10": (157757.62, 157757.62),
    "i3001500_11": (150015.13, 150015.13), "i3001500_12": (154937.67, 154937.67), "i3001500_13": (151608.42, 151608.42),
    "i3001500_14": (151848.05, 151848.05), "i3001500_15": (156480.89, 156480.89), "i3001500_16": (155493.77, 155493.77),
    "i3001500_17": (156038.04, 156038.04), "i3001500_18": (156790.75, 156790.75), "i3001500_19": (155947.13, 155947.13),
    "i3001500_20": (156426.14, 156426.14),
}


def _gs_rows(fname: str):
    """Las filas `nombre & |J| & |I| & valor [& mejor UB] \\` de un archivo de OR-Brescia."""
    for line in (REFS / fname).read_text().splitlines():
        cells = [c.strip() for c in line.replace("\\", "").split("&")]
        if len(cells) >= 4 and re.fullmatch(r"[\w]+", cells[0]) and cells[0] != "Name":
            yield cells


def literature() -> dict[str, list[dict]]:
    """Todas las referencias de la literatura, por instancia: [{"lb", "ub", "opt", "source"}]."""
    refs: dict[str, list[dict]] = {}

    def add(name, lb=None, ub=None, opt=False, source=""):
        refs.setdefault(name, []).append({"lb": lb, "ub": ub, "opt": opt, "source": source})

    for fname, rename in (("Holmberg_Solution_Values.txt", lambda n: f"H-{n}"),
                          ("Yang_Solution_Values.txt", lambda n: f"Y-{n}"),
                          ("OR-Library_Solution_Values.txt", lambda n: n)):
        for cells in _gs_rows(fname):
            v = float(cells[3])
            add(rename(cells[0]), v, v, True, GS)
    for cells in _gs_rows("TBED1_Solution_Values.txt"):
        opt = "(*)" in cells[3]
        add(cells[0], float(cells[3].replace("(*)", "")), float(cells[4]), opt, GS)
    for k, v in KONG_TB4.items():
        lb, ub = v if isinstance(v, tuple) else (v, v)
        add(f"TB4-{k}", lb, ub, lb == ub, KONG)
    for k, v in KONG_TBED1_OPT.items():
        add(k, v, v, True, KONG)
    for k, (lb, ub) in KONG_TBED1.items():
        add(k, lb, ub, False, KONG)
    sols = REFS / "kong2021_tbed1_solutions.json"
    if sols.exists():
        from . import model_parts as ref

        for k, sol in json.loads(sols.read_text()).items():
            path = BENCH / f"{k}.txt"
            if path.exists():  # las TBED1 se bajan con `fetch --large`; sin la instancia no se puede evaluar
                inst = SSCFLPInstance.load(str(path))
                sol = ref.wrap(sol)
                assert not any(ref.violations(inst, sol).values()), k
                add(k, None, round(sum(ref.cost_terms(inst, sol).values()), 6), False, KONG + ", solución")
    return refs


def combine(refs: list[dict]) -> dict:
    lbs = [r["lb"] for r in refs if r["lb"] is not None]
    ubs = [r["ub"] for r in refs if r["ub"] is not None]
    lb, ub = (max(lbs) if lbs else None), (min(ubs) if ubs else None)
    # los valores publicados vienen con 2 decimales: óptimo si alguna fuente lo prueba o si la brecha es de redondeo
    opt = any(r["opt"] for r in refs) or (lb is not None and ub is not None and ub - lb <= 0.01)
    if opt and lb is not None and ub is not None:
        lb = min(lb, ub)
    return {"ub": ub, "lb": lb, "opt": opt, "source": "; ".join(sorted({r["source"] for r in refs}))}


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
    sol = ref.wrap([max(I, key=lambda i: x[i, j].value() or 0.0) for j in J])
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

    data = {"_fuente": "examples/sscflp/best_known.py: Guastaroba y Speranza (2014, OR-Brescia), Kong (2021, "
                       "arXiv:2112.12974) y CBC (D-). ub = mejor solución conocida, lb = mejor cota inferior, "
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
        for name, refs in literature().items():
            if name in entries and entries[name].get("source", "").startswith("CBC"):
                refs.append(entries[name])
            entries[name] = combine(refs)
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
