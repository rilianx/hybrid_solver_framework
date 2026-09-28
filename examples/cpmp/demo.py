"""CPMP: estrategias constructivas del framework sobre instancias al estilo CVS.

    python -m examples.cpmp.demo                         # tamaños 3×5, 5×5, 5×7, 6×6; 10 instancias
    python -m examples.cpmp.demo --sizes 5x7 10x6 --n 20 --beam 5 20

Todo corre sobre la misma vista neutral (solo movimientos simples). Cambia la estrategia
del framework y el puntaje que usa:

- `best_first`: el respaldo neutral de la vista, desde el layout inicial;
- FRG⁻ / FRG: la referencia escrita a mano (Araya y Toledo 2023), como constructor;
- greedy del framework con los puntajes `frg_policy` (= FRG paso a paso) y `destination_rank`;
- beam search clásica (puntaje acumulado de `destination_rank`);
- beam search greedy: hijos ordenados y podados por `destination_rank` (`branching` = 2S) y
  evaluados con el rollout greedy de `destination_rank` o de `frg_policy` (= BS-FRG con
  movimientos simples).

Un puntaje generado por el LLM entra en los mismos lugares que `destination_rank`. LB es la
cota trivial (mal puestos); "fallas" son construcciones infactibles (el respaldo neutral no
alcanzó a ordenar).
"""

from __future__ import annotations

import argparse
import time
from random import Random
from statistics import mean

from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor

from .catalog import BestFirstConstructor
from .construction import DestinationRank, FRGConstructor, FRGPolicy
from .instance import CPMPInstance
from .layout import Layout
from .problem_model import CPMPModel


def strategies(P: CPMPModel, beams: list[int], S: int):
    out = [
        ("best_first", BestFirstConstructor(P)),
        ("FRG⁻", FRGConstructor(P, prevent=False, assignment="never")),
        ("FRG", FRGConstructor(P)),
        ("greedy frg_policy", GreedyConstructor(P, FRGPolicy(P))),
        ("greedy destination_rank", GreedyConstructor(P, DestinationRank(P))),
    ]
    for nb in beams:
        out += [
            (f"beam clásica destination_rank nb={nb}",
             BeamSearchConstructor(P, DestinationRank(P), evaluation="score", beam_width=nb, branching=2 * S)),
            (f"beam greedy destination_rank nb={nb}",
             BeamSearchConstructor(P, DestinationRank(P), beam_width=nb, branching=2 * S)),
            (f"BS-FRG (rollout frg_policy) nb={nb}",
             BeamSearchConstructor(P, DestinationRank(P), rollout=FRGPolicy(P), beam_width=nb, branching=2 * S)),
        ]
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sizes", nargs="+", default=["3x5", "5x5", "5x7", "6x6"], help="SxH (pilas × altura)")
    ap.add_argument("--n", type=int, default=10, help="instancias por tamaño")
    ap.add_argument("--beam", type=int, nargs="+", default=[5], help="anchos de haz nb")
    args = ap.parse_args(argv)

    for size in args.sizes:
        S, H = (int(v) for v in size.lower().split("x"))
        insts = [CPMPInstance.cvs_like(S, H, Random(1000 + i)) for i in range(args.n)]
        lb = mean(Layout.from_instance(i).bad() for i in insts)
        rows: dict[str, tuple[list, list]] = {}
        for inst in insts:
            P = CPMPModel(inst)
            for name, c in strategies(P, args.beam, S):
                t0 = time.perf_counter()
                sol = c.build(inst, Random(0))
                dt = time.perf_counter() - t0
                costs, times = rows.setdefault(name, ([], []))
                costs.append(P.objective(sol) if P.is_feasible(sol) else None)
                times.append(dt)
        print(f"\n=== CVS-like {S}×{H}: N = {S * (H - 2)}, {args.n} instancias, LB medio {lb:.1f} ===")
        print(f"{'estrategia':<42} {'movs':>8} {'fallas':>7} {'s/inst':>8}")
        for name, (costs, times) in rows.items():
            ok = [c for c in costs if c is not None]
            avg = f"{mean(ok):8.2f}" if ok else f"{'—':>8}"
            print(f"{name:<42} {avg} {costs.count(None):>7} {mean(times):8.3f}")


if __name__ == "__main__":
    main()
