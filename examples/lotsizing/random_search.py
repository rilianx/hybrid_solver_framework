"""Búsqueda aleatoria sobre el espacio de diseño completo del CLSP: la versión
mínima del *target runner* de §8, y el baseline contra el que se comparará
irace/Optuna cuando se integren.

    python -m examples.lotsizing.random_search --configs 12 --budget 5

Muestrea configuraciones del `ConfigSpace` (esqueleto + componentes + parámetros,
con condicionalidad), las ensambla y evalúa sobre instancias de entrenamiento
con presupuesto homogéneo, y reporta el ranking. Si hay componentes generados
por LLM en `generated/clsp/`, entran al catálogo automáticamente.
"""

from __future__ import annotations

import argparse
from random import Random

from config_space import suggest_from_space
from core.assembler import Assembler, describe

from .catalog import build_registry, load_generated
from .problem_model import CLSPInstance, LotSizingModel


class RandomTrial:
    """Doble mínimo de `optuna.Trial` para muestrear el espacio al azar."""

    def __init__(self, rng: Random):
        self.rng = rng

    def suggest_int(self, name, low, high, *, log=False):
        return self.rng.randint(low, high)

    def suggest_float(self, name, low, high, *, log=False):
        if log and low > 0:
            import math

            return math.exp(self.rng.uniform(math.log(low), math.log(high)))
        return self.rng.uniform(low, high)

    def suggest_categorical(self, name, choices):
        return self.rng.choice(list(choices))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", type=int, default=12)
    ap.add_argument("--budget", type=float, default=5.0, help="segundos por corrida")
    ap.add_argument("--train", type=int, default=2, help="instancias de entrenamiento")
    ap.add_argument("--items", type=int, default=8)
    ap.add_argument("--periods", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--generated", default="generated/clsp")
    args = ap.parse_args()

    generated = load_generated(args.generated)
    registry = build_registry(generated)
    if generated:
        print(f"Componentes LLM en el catálogo: {[c.name for c in generated]}")
    assembler = Assembler(problem_factory=LotSizingModel, registry=registry)
    space = assembler.config_space()
    print(f"Esqueletos disponibles: {assembler.available_skeletons()}; parámetros en el espacio: {len(space.nodes)}\n")

    rng = Random(args.seed)
    train = [CLSPInstance.trigeiro(args.items, args.periods, Random(100 + k), utilization=0.95, tbo=3.0) for k in range(args.train)]

    results = []
    for k in range(args.configs):
        config = suggest_from_space(space, RandomTrial(Random(rng.randrange(10**9))))
        cost = assembler.evaluate(config, train, args.budget, seed=args.seed)
        results.append((cost, config))
        print(f"{k + 1:>3}. {describe(config):<70} costo medio={cost:>12.1f}")

    results.sort(key=lambda r: r[0])
    print("\nMejores 3 configuraciones:")
    for cost, config in results[:3]:
        print(f"  {cost:>12.1f}  {config}")


if __name__ == "__main__":
    main()
