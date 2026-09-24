"""Muestreo de vecindarios (`core.neighborhood`): los esqueletos no recorren `moves` completo."""

from __future__ import annotations

from random import Random

from core.neighborhood import random_move, sample_moves
from core.validation import ValidationContext, validate_component
from examples.knapsack.components import COMPONENT_BIT_FLIP_NEIGHBORHOOD, BitFlipNeighborhood, GreedyRandomizedConstructor
from examples.knapsack.problem_model import KnapsackInstance, KnapsackModel, KnapsackObjective, bound_problem_model
from skeletons.ils import hill_climb


class Counting:
    """Vecindario de juguete: minimizar sum(sol) con flips; cuenta cuántos `delta` se piden."""

    def __init__(self):
        self.deltas = 0

    def moves(self, sol):
        return [(i,) for i in range(len(sol))]

    def apply(self, sol, m):
        return sol[: m[0]] + (1 - sol[m[0]],) + sol[m[0] + 1:]

    undo = apply

    def delta(self, sol, m):
        self.deltas += 1
        return 1 - 2 * sol[m[0]]


def test_sample_moves_is_a_random_subset_and_full_when_small():
    nbh, sol = Counting(), (1,) * 50
    got = sample_moves(nbh, sol, 8, Random(0))
    assert len(got) == len(set(got)) == 8 and set(got) <= set(nbh.moves(sol))
    assert got == sample_moves(nbh, sol, 8, Random(0)) != sample_moves(nbh, sol, 8, Random(1))
    assert sample_moves(nbh, sol, 100, Random(0)) == nbh.moves(sol) == sample_moves(nbh, sol, None, Random(0))
    assert random_move(nbh, (), Random(0)) is None


def test_neighborhood_sample_method_is_used_when_present():
    class Sampled(Counting):
        def sample(self, sol, k, rng):
            return [(0,)][:k]

    assert sample_moves(Sampled(), (1, 1), 5, Random(0)) == [(0,)]
    assert random_move(Sampled(), (1, 1), Random(0)) == (0,)


def test_sampled_hill_climb_evaluates_fewer_moves_per_step():
    full, sampled = Counting(), Counting()
    sol = (1,) * 200
    a = hill_climb(None, full, strategy="best", max_iters=3)(sol, Random(0))
    b = hill_climb(None, sampled, strategy="best", max_iters=3, sample_size=10)(sol, Random(0))
    assert sum(a) == sum(b) == 197
    assert full.deltas == 600 and sampled.deltas == 30


def test_validator_checks_the_optional_sample_method():
    inst = KnapsackInstance.random(8, Random(5))
    evaluator = KnapsackObjective(KnapsackModel(), inst)
    ctx = ValidationContext(problem=bound_problem_model(inst), instances=[inst],
                            trivial_solutions=[tuple(False for _ in range(inst.n))],
                            baseline_constructor=GreedyRandomizedConstructor(alpha=1.0))

    class GoodSample(BitFlipNeighborhood):
        def sample(self, sol, k, rng):
            ms = list(self.moves(sol))
            return rng.sample(ms, min(k, len(ms)))

    class BadSample(BitFlipNeighborhood):
        def sample(self, sol, k, rng):
            return [(99, True)] * k

    good = validate_component(COMPONENT_BIT_FLIP_NEIGHBORHOOD, GoodSample(evaluator), ctx)
    assert "neighborhood.sample" not in {c.name for c in good.failures()}
    bad = validate_component(COMPONENT_BIT_FLIP_NEIGHBORHOOD, BadSample(evaluator), ctx)
    assert bad.failed_layer == "contractual" and any(c.name == "neighborhood.sample" for c in bad.failures())


def test_ls_sample_is_a_skeleton_param_with_explicit_default():
    from core.assembler import SKELETONS
    from core.component import ComponentSpec

    for sk in ("ILS", "VNS", "GRASP"):
        spec = SKELETONS[sk].params["ls_sample"]
        assert ComponentSpec("_", "stop", (), (), {"ls_sample": spec}, None).default_params() == {"ls_sample": 32}
