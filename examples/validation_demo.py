"""Demo de la validación por capas (§7): un componente correcto y tres rotos,
mostrando el texto de retroalimentación que se devolvería al LLM (§6).

Uso: `python -m examples.validation_demo`
"""

from __future__ import annotations

from itertools import product
from random import Random

from core.common_components import MaxTimeStop
from core.validation import ValidationContext, validate_component, validate_problem_model, validate_variant
from examples.knapsack.components import (
    COMPONENT_BIT_FLIP_NEIGHBORHOOD,
    COMPONENT_RANDOM_DESTRUCTION,
    BitFlipNeighborhood,
    GreedyRandomizedConstructor,
    RandomDestruction,
)
from examples.knapsack.problem_model import KnapsackInstance, KnapsackModel, KnapsackObjective, bound_problem_model
from skeletons.sa import build_sa, make_run


def main() -> None:
    inst = KnapsackInstance.random(8, Random(5))
    problem = bound_problem_model(inst)
    evaluator = KnapsackObjective(KnapsackModel(), inst)
    ctx = ValidationContext(
        problem=problem,
        instances=[inst],
        trivial_solutions=[tuple(False for _ in range(inst.n))],
        baseline_constructor=GreedyRandomizedConstructor(alpha=1.0),
        reference_destruction=RandomDestruction(),
        enumerate_solutions=lambda inst: list(product([False, True], repeat=inst.n)),
    )

    print("=== ProblemModel (capa semántica MIP) ===")
    print(validate_problem_model(ctx).feedback(), "\n")

    print("=== Componente correcto ===")
    print(validate_component(COMPONENT_BIT_FLIP_NEIGHBORHOOD, BitFlipNeighborhood(evaluator), ctx).feedback(), "\n")

    class WrongDelta(BitFlipNeighborhood):
        def delta(self, sol, m):
            return -abs(super().delta(sol, m))  # "siempre mejora": error clásico de signo

    print("=== Vecindario con delta incorrecto ===")
    print(validate_component(COMPONENT_BIT_FLIP_NEIGHBORHOOD, WrongDelta(evaluator), ctx).feedback(), "\n")

    class Leaky(RandomDestruction):
        def destroy(self, sol, ratio, rng):
            partial, free = super().destroy(sol, ratio, rng)
            return partial, free | {"x_extra"}

    print("=== Destrucción que inventa variables ===")
    print(validate_component(COMPONENT_RANDOM_DESTRUCTION, Leaky(), ctx).feedback(), "\n")

    class Inert(BitFlipNeighborhood):
        def moves(self, sol):
            return []

    def runner(inst, rng, budget):
        sk, extra = build_sa(problem, GreedyRandomizedConstructor(1.0), Inert(evaluator), MaxTimeStop(budget))
        return make_run(sk, extra)(inst, rng)

    print("=== Variante inerte (capas operativa + calidad) ===")
    print(validate_variant(runner, ctx, name="SA con vecindario vacío", budget_seconds=0.3).feedback())


if __name__ == "__main__":
    main()
