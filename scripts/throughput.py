"""Throughput de los componentes de un catálogo en una instancia de tamaño realista: cuántas
evaluaciones por segundo hace cada vecindario (delta), puntaje (construcción completa),
perturbación y destrucción. Sirve para ver si un catálogo generado pierde por hacer menos
movimientos en el mismo presupuesto.

    python -m scripts.throughput --problem cvrp                                  # escrito a mano
    python -m scripts.throughput --problem cvrp --variant tour --workspace generated/cvrp_tour_cycle2
"""

from __future__ import annotations

import argparse
import itertools
import time
from random import Random


def _rate(fn, seconds: float = 1.0, max_calls: int = 100_000) -> float:
    t0, n = time.perf_counter(), 0
    while n < max_calls and time.perf_counter() - t0 < seconds:
        fn()
        n += 1
    return n / max(time.perf_counter() - t0, 1e-9)


def measure(pack, registry, size: str, seconds: float = 1.0) -> list[dict]:
    from core.construction import GreedyConstructor

    inst = pack.make_instances(1, 4242, pack.parse_size(size))[0]
    P = pack.problem_factory(inst)
    start = pack.baseline_constructor().build(inst, Random(0))
    rows = []
    for spec in registry.for_slot("neighborhood"):
        nb = spec.make(P, **spec.default_params())
        moves = list(itertools.islice(nb.moves(start), 500))
        if not moves:
            continue
        it = itertools.cycle(moves)
        rows.append({"slot": "neighborhood", "name": spec.name,
                     "per_s": _rate(lambda: nb.delta(start, next(it)), seconds), "what": "delta"})
    for spec in registry.for_slot("greedy_score"):
        g = GreedyConstructor(P, spec.make(P, **spec.default_params()))
        rows.append({"slot": "greedy_score", "name": spec.name, "per_s": _rate(lambda: g.build(inst, Random(0)), seconds, 50),
                     "what": "construcciones"})
    for spec in registry.for_slot("perturbation"):
        pt, rng = spec.make(P, **spec.default_params()), Random(0)
        rows.append({"slot": "perturbation", "name": spec.name, "per_s": _rate(lambda: pt.perturb(start, 1.0, rng), seconds),
                     "what": "perturb"})
    # soluciones distintas en cada llamada: PartsModel memoriza el objetivo por solución
    gen = getattr(P, "random_solution", None)
    if callable(gen):
        sols = [gen(Random(s)) for s in range(2000)]
        it_s = iter(sols)
        fresh = pack.problem_factory(inst)
        rows.append({"slot": "modelo", "name": "objective", "per_s": _rate(lambda: fresh.objective(next(it_s)), seconds, len(sols)),
                     "what": "objective (sin caché)"})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="cvrp")
    ap.add_argument("--variant", default=None)
    ap.add_argument("--workspace", default=None)
    ap.add_argument("--size", default="30")
    ap.add_argument("--seconds", type=float, default=1.0)
    args = ap.parse_args()
    from llm.catalog import build_registry, load_generated

    if args.variant:
        from llm.cycle import load_variant

        pack = load_variant(args.problem, args.variant, args.workspace, reference=False)
        registry = build_registry(pack, load_generated(pack, args.workspace, revalidate=False, verbose=False), handwritten=False)
    else:
        from llm.cycle import base_pack

        pack = base_pack(args.problem)
        registry = build_registry(pack)
    for r in measure(pack, registry, args.size, args.seconds):
        print(f"{r['slot']:<13} {r['name']:<42} {r['per_s']:>12,.0f} {r['what']}/s")


if __name__ == "__main__":
    main()
