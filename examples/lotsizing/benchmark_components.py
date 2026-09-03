"""Benchmark de componentes (§7 calidad, §10): ¿los componentes generados
*sirven*, no solo son válidos? Y ¿son realmente distintos entre sí?

Para cada componente de un slot se fija el resto de la variante (mismo
esqueleto, mismos parámetros por defecto, mismo presupuesto, mismas
instancias) y se compara el costo. Además se mide la diversidad
estructural entre componentes del mismo slot:

- neighborhood: Jaccard entre los conjuntos de vecinos que producen desde
  la misma solución (1.0 = mismo vecindario con otro nombre).
- destruction: Jaccard medio entre los `free_vars` que liberan con las
  mismas semillas y ratio.

    python -m examples.lotsizing.benchmark_components --budget 10 --train 2
"""

from __future__ import annotations

import argparse
from itertools import combinations
from random import Random
from statistics import mean

from core.assembler import Assembler

from .catalog import build_registry, load_generated
from .components import LotForLotConstructor
from .problem_model import CLSPInstance, LotSizingModel

SLOT_TO_SKELETON = {"neighborhood": "SA", "destruction": "LNS_MIP", "perturbation": "ILS", "constructor": "LNS_MIP", "fixing_policy": "FIX_OPT"}


from core.validation.diversity import signature, similarity


def diversity_table(registry, slot: str, inst) -> list[tuple[str, str, float]]:
    problem = LotSizingModel(inst)
    sol = LotForLotConstructor().build(inst, Random(0))
    specs = registry.for_slot(slot)
    sigs = {}
    for spec in specs:
        comp = spec.make(problem, **spec.default_params())
        sig = signature(slot, comp, sol, problem)
        if sig:
            sigs[spec.name] = sig
    rows = []
    for a, b in combinations(sigs, 2):
        rows.append((a, b, similarity(sigs[a], sigs[b])))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", nargs="+", default=["neighborhood", "destruction"])
    ap.add_argument("--budget", type=float, default=10.0)
    ap.add_argument("--train", type=int, default=2)
    ap.add_argument("--items", type=int, default=10)
    ap.add_argument("--periods", type=int, default=15)
    ap.add_argument("--generated", default="generated/clsp")
    args = ap.parse_args()

    generated = load_generated(args.generated, verbose=True)
    registry = build_registry(generated)
    gen_names = {c.name for c in generated}
    assembler = Assembler(problem_factory=LotSizingModel, registry=registry)
    train = [CLSPInstance.trigeiro(args.items, args.periods, Random(100 + k), utilization=0.95, tbo=3.0) for k in range(args.train)]

    for slot in args.slots:
        skeleton = SLOT_TO_SKELETON[slot]
        print(f"\n=== slot {slot} (esqueleto fijo: {skeleton}, {args.budget:.0f}s × {args.train} instancias) ===")
        base = LotForLotConstructor()
        baseline = mean(LotSizingModel(i).objective(base.build(i, Random(0))) for i in train)
        print(f"{'lot-for-lot (sin búsqueda)':<45} {baseline:>12.1f}")
        rows = []
        for spec in registry.compatible(slot, skeleton):
            config = assembler.default_config(skeleton, choices={slot: spec.name})
            cost = assembler.evaluate(config, train, args.budget, seed=0)
            raw = None
            if slot == "constructor":
                # Con búsqueda encima, 10 s de LNS-MIP borran la diferencia entre puntos de partida
                # (corrida 7: los 4 constructores dieron exactamente 72197,0). Lo que distingue a
                # un constructor es la solución que entrega SIN búsqueda, y si es factible.
                # ligado al ProblemModel de CADA instancia, como hace el Assembler
                built = [(LotSizingModel(i), spec.make(LotSizingModel(i), **spec.default_params()).build(i, Random(0))) for i in train]
                raw = (mean(P.objective(sol) for P, sol in built), sum(P.is_feasible(sol) for P, sol in built))
            rows.append((cost, spec.name, raw))
        for cost, name, raw in sorted(rows, key=lambda r: (r[0], r[2][0] if r[2] else 0)):
            tag = " [LLM]" if name in gen_names else ""
            extra = ""
            if raw is not None:
                extra = f"   | sin búsqueda: {raw[0]:>10.1f} ({(baseline - raw[0]) / baseline:+.1%}), factible en {raw[1]}/{len(train)}"
            print(f"{name + tag:<45} {cost:>12.1f}   ({(baseline - cost) / baseline:+.1%} vs lot-for-lot){extra}")

        div = diversity_table(registry, slot, train[0])
        if div:
            print(f"\n  diversidad (similitud estructural; 1.0 = idénticos):")
            for a, b, j in sorted(div, key=lambda r: -r[2]):
                flag = "  <-- casi duplicados" if j > 0.8 else ""
                print(f"  {a:<32} vs {b:<32} {j:.2f}{flag}")


if __name__ == "__main__":
    main()
