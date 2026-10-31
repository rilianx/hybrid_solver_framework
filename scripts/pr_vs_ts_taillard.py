"""PR (sin afinar) contra las TS afinadas de la run 55, mismo catálogo a mano y mismo presupuesto, en Taillard.

    python scripts/pr_vs_ts_taillard.py 30 ta01,ta02,...,ta10 out.json      # 3 semillas, 4 procesos
"""
import sys, json; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from concurrent.futures import ProcessPoolExecutor
from random import Random
from statistics import mean

TAILLARD_BK = __import__('pathlib').Path(__file__).resolve().parent.parent / 'examples/jobshop/taillard/best_known.json'
TS1 = {'skeleton': 'TS', 'constructor': 'job_order', 'neighborhood': 'critical_swap', 'TS.tenure': 9, 'TS.candidate_size': 82, 'TS.estimate_top': 7, 'TS.elite_size': 7, 'TS.stall': 2831}
TS2 = {'skeleton': 'TS', 'constructor': 'job_order', 'neighborhood': 'critical_swap', 'TS.tenure': 10, 'TS.candidate_size': 29, 'TS.estimate_top': 2, 'TS.elite_size': 6, 'TS.stall': 1176}
PRB = {'skeleton': 'PR', 'constructor': 'job_order', 'neighborhood': 'critical_swap', 'relink': 'machine_order', 'PR.tenure': 9, 'PR.candidate_size': 82, 'PR.estimate_top': 7}
CFG = {"TS_r1": TS1, "TS_r2": TS2, "PR_2k": dict(PRB, **{"PR.ts_iters": 2000}), "PR_10k": dict(PRB, **{"PR.ts_iters": 10000})}
def run(a):
    label, name, seed, budget = a
    from examples.jobshop.instance import JSSPInstance
    from examples.jobshop.pack import PACK
    from tuning.cli import make_assembler
    from scripts.taillard_eval import TAILLARD
    A, _ = make_assembler(PACK, "handwritten", None, native=True)
    inst = JSSPInstance.load(str(TAILLARD / f"{name}.txt"))
    r = A.assemble(CFG[label])(inst, Random(seed), budget)
    return label, name, seed, PACK.problem_factory(inst).objective(r.best_solution), r.iterations
if __name__ == "__main__":
    budget = float(sys.argv[1]); insts = sys.argv[2].split(",")
    jobs = [(l, n, s, budget) for n in insts for s in range(3) for l in CFG]
    with ProcessPoolExecutor(4) as ex:
        rows = list(ex.map(run, jobs))
    json.dump(rows, open(sys.argv[3], "w"))
    bk = json.load(open(TAILLARD_BK))
    for l in CFG:
        g = [100 * (mk - bk[n]) / bk[n] for (ll, n, s, mk, it) in rows if ll == l]
        print(l, round(mean(g), 3))
