"""PR con los relinks generados por el LLM (corrida 112), sobre el N5 generado y optimizado, en Taillard.

    python scripts/pr_relinks_taillard.py 30 ta01,ta02,...,ta10 out.json      # 3 semillas, 4 procesos
"""
import sys, json; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from concurrent.futures import ProcessPoolExecutor
from random import Random
from statistics import mean

TAILLARD_BK = __import__('pathlib').Path(__file__).resolve().parent.parent / 'examples/jobshop/taillard/best_known.json'
N5 = {'skeleton': 'PR', 'constructor': 'trivial', 'neighborhood': 'critical_path_adjacent_swap',
      'critical_path_adjacent_swap.block_ends_only': 1, 'PR.tenure': 9, 'PR.candidate_size': 82, 'PR.estimate_top': 7,
      'PR.ts_iters': 10000}
CFG = {r: dict(N5, relink=r) for r in ("kendall_adjacent_swap_relink", "lis_insertion_relink", "hamming_position_swap_relink")}
def run(a):
    label, name, seed, budget = a
    from examples.jobshop.instance import JSSPInstance
    from examples.jobshop.pack import PACK
    from tuning.cli import make_assembler
    from scripts.taillard_eval import TAILLARD
    A, _ = make_assembler(PACK, "generated", "generated/jobshop_native", native=True)
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
