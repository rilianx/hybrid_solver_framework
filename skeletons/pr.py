"""PR (path relinking con población de élite), como en `native/include/hsf/core.hpp` (`path_relinking`).

Slots: Constructor, Vecindario (la mejora con tabú, `skeletons/ts.py`) y Relink (`distance(a, b)` y
`step(cur, guide, rng)`: cuánto difieren dos soluciones y un paso de una hacia la otra). Nada del problema:

    población ← PR.pop_size soluciones (la partida y construcciones nuevas con PR.init_moves movimientos al
                azar del vecindario), cada una mejorada con PR.ts_iters iteraciones de tabú, sin repetidas
    mientras quede tiempo:
        A, B ← dos de la población al azar
        camino de A a B: en cada paso, la mejor (por objetivo) de PR.path_cands soluciones un paso más cerca
        elegida ← la mejor del tramo central del camino (a más de PR.band de la distancia de A y de B)
        mejorada ← tabú desde elegida
        si mejorada es mejor que la peor de la población y no está repetida: reemplaza a la peor

Es la idea de i-TSAB (Nowicki y Smutnicki, 2005) y de TS/PR (Peng, Lü y Cheng, 2015) en el job shop, y de GRASP
con path relinking en general (Resende y Ribeiro).
"""

from __future__ import annotations

import math
import time
from random import Random

from core.common_components import AnyStop, MaxIterationsStop, MaxTimeStop
from core.contracts import Constructor, Neighborhood, ProblemModel
from core.skeleton import RunResult

from .ts import build_ts


class _Given:
    def __init__(self, sol):
        self.sol = sol

    def build(self, inst, rng: Random):
        return self.sol


def run_pr(problem: ProblemModel, constructor: Constructor, neighborhood: Neighborhood, relink, inst, rng: Random,
           budget: float, pop_size: int = 10, ts_iters: int = 1000, tenure: int = 10, candidate_size: int = 30,
           estimate_top: int = 0, path_cands: int = 1, band: float = 0.25, init_moves: int = 20) -> RunResult:
    t0 = time.monotonic()
    left = lambda: budget - (time.monotonic() - t0)  # noqa: E731
    stats = {"iterations": 0}
    start = constructor.build(inst, rng)
    best = [start, problem.objective(start)]

    def improve(sol):
        stop = AnyStop((MaxIterationsStop(ts_iters), MaxTimeStop(max(0.0, left()))))
        res = build_ts(problem, _Given(sol), neighborhood, stop, tenure=tenure, candidate_size=candidate_size,
                       estimate_top=estimate_top).run(inst, rng)
        stats["iterations"] += res.iterations
        if res.best_objective < best[1]:
            best[0], best[1] = res.best_solution, res.best_objective
        return res.best_solution, res.best_objective

    pop: list[tuple] = []
    repeated = lambda s: any(relink.distance(s, p) == 0 for p, _ in pop)  # noqa: E731
    for i in range(max(2, pop_size)):
        if left() <= 0:
            break
        s = start if i == 0 else constructor.build(inst, rng)
        for _ in range(0 if i == 0 else init_moves):
            moves = list(neighborhood.moves(s))
            if not moves:
                break
            s = neighborhood.apply(s, moves[rng.randrange(len(moves))])
        p = improve(s)
        if not repeated(p[0]):
            pop.append(p)
    while left() > 0 and len(pop) >= 2:
        a, b = rng.sample(range(len(pop)), 2)
        cur, guide = pop[a][0], pop[b][0]
        d0 = d = relink.distance(cur, guide)
        lo = max(1, math.ceil(band * d0))
        hi = max(lo, d0 - lo)
        pick, f_pick = cur, math.inf
        while d > 0 and d0 - d < hi and left() > 0:
            cands = [relink.step(cur, guide, rng) for _ in range(max(1, path_cands))]
            scored = [(problem.objective(x), k) for k, x in enumerate(cands)]
            f_nxt, k = min(scored)
            nxt = cands[k]
            dn = relink.distance(nxt, guide)
            if dn >= d:
                raise RuntimeError("relink: el paso no acercó la solución a la guía")
            cur, d = nxt, dn
            if d0 - d >= lo and f_nxt < f_pick:
                pick, f_pick = cur, f_nxt
        if left() <= 0:
            break
        p = improve(pick)
        worst = max(range(len(pop)), key=lambda i: pop[i][1])
        if p[1] < pop[worst][1] and not repeated(p[0]):
            pop[worst] = p
    return RunResult(best_solution=best[0], best_objective=best[1], iterations=stats["iterations"],
                     elapsed_time=time.monotonic() - t0, accepted=0)
