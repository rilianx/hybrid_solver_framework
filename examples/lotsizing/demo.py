"""Demo del piloto CLSP: compara variantes del mismo esqueleto con el mismo
presupuesto de tiempo de pared (§8: "presupuesto por corrida homogéneo entre
variantes heurísticas y matheurísticas"), incluido el híbrido Relax-and-Fix →
Fix-and-Optimize que la §5.2 promete "gratis", y el MIP completo con el mismo
tiempo como referencia (§9.4b).

Uso:
    python -m examples.lotsizing.demo             # instancia Trigeiro 15×20, 20 s por variante
    python -m examples.lotsizing.demo --easy      # instancia aleatoria pequeña
    python -m examples.lotsizing.demo --budget 60 --items 15 --periods 20
"""

from __future__ import annotations

import argparse
import time
from random import Random

from core.common_components import (
    AlwaysAccept,
    BetterAcceptance,
    MIPModelRepair,
    MaxTimeStop,
)
from core.fixing_policies import SlidingWindowPolicy
from skeletons.fix_and_optimize import build_fix_and_optimize, run_fix_and_optimize
from skeletons.ils import build_ils, hill_climb
from skeletons.lns_mip import build_lns_mip, run_lns_mip
from skeletons.relax_and_fix import RelaxAndFixConstructor
from skeletons.sa import build_sa, make_run

from .components import (
    LotForLotConstructor,
    PeriodWindowDestruction,
    RandomSetupDestruction,
    SetupFlipNeighborhood,
    SetupFlipPerturbation,
)
from .problem_model import CLSPInstance, LotSizingModel


def timed(label, fn, problem):
    t0 = time.perf_counter()
    result = fn()
    feas = problem.is_feasible(result.best_solution)
    print(
        f"{label:<40} costo={result.best_objective:>10.1f}  iters={result.iterations:<5d} "
        f"t={time.perf_counter() - t0:5.1f}s  factible={feas}"
    )
    return result


def run_demo(inst: CLSPInstance, budget: float, seed: int = 3) -> None:
    problem = LotSizingModel(inst)
    print(
        f"CLSP: {inst.n_items} ítems × {inst.n_periods} períodos, "
        f"capacidad={inst.capacity[0]:.0f}/período, presupuesto={budget:.0f}s por variante\n"
    )

    lfl = LotForLotConstructor()
    print(f"{'Lot-for-lot (constructor base)':<40} costo={problem.objective(lfl.build(inst, Random(seed))):>10.1f}")

    # Relax-and-Fix como constructor: presupuesto total repartido entre ventanas.
    n_windows = inst.n_periods - 1
    rf = RelaxAndFixConstructor(
        problem, SlidingWindowPolicy(window_size=2, overlap=1),
        time_limit_per_window=max(1.0, budget / n_windows), fallback=lfl,
    )
    t0 = time.perf_counter()
    rf_sol = rf.build(inst, Random(seed))
    print(
        f"{'Relax-and-Fix (constructor)':<40} costo={problem.objective(rf_sol):>10.1f}  {'':<11} "
        f"t={time.perf_counter() - t0:5.1f}s  factible={problem.is_feasible(rf_sol)}"
    )
    rf_time = time.perf_counter() - t0

    nbh = SetupFlipNeighborhood(problem)
    sub_mip_tl = max(1.0, budget / 10)

    sa, extra = build_sa(problem, lfl, nbh, MaxTimeStop(budget), T0=200.0, alpha=0.995)
    timed("SA (lot-for-lot + setup_flip)", lambda: make_run(sa, extra)(inst, Random(seed)), problem)

    ils = build_ils(problem, lfl, hill_climb(problem, nbh, "first", max_seconds=budget / 10), SetupFlipPerturbation(),
                    BetterAcceptance(), MaxTimeStop(budget), strength=2)
    timed("ILS (HC first-improvement)", lambda: ils.run(inst, Random(seed)), problem)

    lns_r = build_lns_mip(problem, lfl, RandomSetupDestruction(inst), MIPModelRepair(problem),
                          BetterAcceptance(), MaxTimeStop(budget), destroy_ratio=0.25, mip_time_limit=sub_mip_tl)
    timed("LNS-MIP (destrucción aleatoria)", lambda: run_lns_mip(lns_r, inst, Random(seed), 0.25), problem)

    lns_w = build_lns_mip(problem, lfl, PeriodWindowDestruction(inst), MIPModelRepair(problem),
                          BetterAcceptance(), MaxTimeStop(budget), destroy_ratio=0.25, mip_time_limit=sub_mip_tl)
    timed("LNS-MIP (destrucción por ventana)", lambda: run_lns_mip(lns_w, inst, Random(seed), 0.25), problem)

    # Híbrido: Relax-and-Fix construye (ya gastó rf_time), Fix-and-Optimize mejora con el resto.
    fo = build_fix_and_optimize(problem, rf, SlidingWindowPolicy(2, 1), BetterAcceptance(),
                                MaxTimeStop(max(1.0, budget - rf_time)), block_size=3, time_limit=sub_mip_tl)
    timed("Relax-and-Fix -> Fix-and-Optimize", lambda: run_fix_and_optimize(fo, inst, Random(seed)), problem)

    t0 = time.perf_counter()
    x = problem.mip.solve(fixed={}, integer=set(problem.mip.variables()), relaxed=set(), time_limit=budget)
    full = problem.objective(problem.from_assignment(x))
    print(f"{f'MIP completo (CBC, {budget:.0f}s)':<40} costo={full:>10.1f}  {'':<11} t={time.perf_counter() - t0:5.1f}s")
    print(f"\nEvaluaciones LP cacheadas: {problem.evaluations}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--easy", action="store_true", help="instancia aleatoria pequeña (4×8)")
    ap.add_argument("--items", type=int, default=15)
    ap.add_argument("--periods", type=int, default=20)
    ap.add_argument("--utilization", type=float, default=0.95)
    ap.add_argument("--tbo", type=float, default=3.0)
    ap.add_argument("--budget", type=float, default=20.0)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    rng = Random(args.seed)
    if args.easy:
        inst = CLSPInstance.random(4, 8, rng)
    else:
        inst = CLSPInstance.trigeiro(args.items, args.periods, rng, utilization=args.utilization, tbo=args.tbo)
    run_demo(inst, args.budget, args.seed)


if __name__ == "__main__":
    main()
