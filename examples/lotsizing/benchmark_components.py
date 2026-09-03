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


from core.validation.diversity import jaccard, signature


def diversity_table(registry, slot: str, inst) -> list[tuple[str, str, float]]:
    problem = LotSizingModel(inst)
    sol = LotForLotConstructor().build(inst, Random(0))
    specs = registry.for_slot(slot)
    sigs = {}
    for spec in specs:
        comp = spec.make(problem, **spec.default_params())
        sig = signature(slot, comp, sol)
        if sig:
            sigs[spec.name] = sig
    rows = []
    for a, b in combinations(sigs, 2):
        rows.append((a, b, jaccard(sigs[a], sigs[b])))
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
            rows.append((cost, spec.name))
        for cost, name in sorted(rows):
            tag = " [LLM]" if name in gen_names else ""
            print(f"{name + tag:<45} {cost:>12.1f}   ({(baseline - cost) / baseline:+.1%} vs lot-for-lot)")

        div = diversity_table(registry, slot, train[0])
        if div:
            print(f"\n  diversidad (Jaccard; 1.0 = idénticos):")
            for a, b, j in sorted(div, key=lambda r: -r[2]):
                flag = "  <-- casi duplicados" if j > 0.8 else ""
                print(f"  {a:<32} vs {b:<32} {j:.2f}{flag}")


if __name__ == "__main__":
    main()
