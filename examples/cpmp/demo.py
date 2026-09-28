"""CPMP: estrategias constructivas del framework sobre instancias al estilo CVS.

    python -m examples.cpmp.demo                         # tamaños 3×5, 5×5, 5×7, 6×6, 10×6; 10 instancias
    python -m examples.cpmp.demo --sizes 5x7 10x6 --n 20 --beam 10 50

Compara, en movimientos medios (menor es mejor) y segundos por instancia:
FRG⁻ y FRG (con la asignación como respaldo); el bucle greedy del framework con los
puntajes `frg_policy` (= FRG paso a paso) y `fill_first`; beam search clásica (puntaje
acumulado de `fill_first`); y la beam search greedy con rollout FRG: BSs-FRG (solo
movimientos simples, k = 3) y BS*-FRG (simples + la iteración de FRG + reducciones R_s).
LB es la cota trivial (mal puestos).
"""

from __future__ import annotations

import argparse
import time
from random import Random
from statistics import mean

from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor

from .construction import FillFirst, FRGConstructor, FRGPolicy
from .frg import Layout
from .instance import CPMPInstance
from .problem_model import CPMPModel


def strategies(P: CPMPModel, beams: list[int], k: int):
    out = [
        ("FRG⁻", FRGConstructor(prevent=False, assignment="never")),
        ("FRG", FRGConstructor()),
        ("greedy frg_policy", GreedyConstructor(P, FRGPolicy(P))),
        ("greedy fill_first", GreedyConstructor(P, FillFirst(P))),
    ]
    for nb in beams:
        out += [
            (f"BS clásica fill_first nb={nb}", BeamSearchConstructor(P, FillFirst(P), evaluation="score", beam_width=nb)),
            (f"BSs-FRG nb={nb}", BeamSearchConstructor(P, rollout="complete", beam_width=nb,
                                                       view_params={"k": k, "compound": False, "frg_action": False})),
            (f"BS*-FRG nb={nb}", BeamSearchConstructor(P, rollout="complete", beam_width=nb, view_params={"k": k})),
        ]
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sizes", nargs="+", default=["3x5", "5x5", "5x7", "6x6", "10x6"], help="SxH (pilas × altura)")
    ap.add_argument("--n", type=int, default=10, help="instancias por tamaño")
    ap.add_argument("--beam", type=int, nargs="+", default=[5], help="anchos de haz nb")
    ap.add_argument("--k", type=int, default=3, help="destinos por pila de origen en los movimientos simples")
    args = ap.parse_args(argv)

    for size in args.sizes:
        S, H = (int(v) for v in size.lower().split("x"))
        insts = [CPMPInstance.cvs_like(S, H, Random(1000 + i)) for i in range(args.n)]
        lb = mean(Layout.from_instance(i).bad() for i in insts)
        rows: dict[str, tuple[list, list]] = {}
        for inst in insts:
            P = CPMPModel(inst)
            for name, c in strategies(P, args.beam, args.k):
                t0 = time.perf_counter()
                sol = c.build(inst, Random(0))
                dt = time.perf_counter() - t0
                costs, times = rows.setdefault(name, ([], []))
                costs.append(P.objective(sol) if P.is_feasible(sol) else None)
                times.append(dt)
        print(f"\n=== CVS-like {S}×{H}: N = {S * (H - 2)}, {args.n} instancias, LB medio {lb:.1f} ===")
        print(f"{'estrategia':<30} {'movs':>8} {'fallas':>7} {'s/inst':>8}")
        for name, (costs, times) in rows.items():
            ok = [c for c in costs if c is not None]
            avg = f"{mean(ok):8.2f}" if ok else f"{'—':>8}"
            print(f"{name:<30} {avg} {costs.count(None):>7} {mean(times):8.3f}")


if __name__ == "__main__":
    main()
