"""Muestreo de vecindarios (`core.neighborhood`): los esqueletos no recorren `moves` completo."""

from __future__ import annotations

from random import Random

from core.neighborhood import random_move, sample_moves
from core.validation import validate_component
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
    from examples.lotsizing.components import COMPONENT_SETUP_FLIP, SetupFlipNeighborhood
    from tests.contexts import clsp_contexts

    ctx = clsp_contexts(n_contexts=1, strict=False)[0]

    class GoodSample(SetupFlipNeighborhood):
        def sample(self, sol, k, rng):
            ms = list(self.moves(sol))
            return rng.sample(ms, min(k, len(ms)))

    class BadSample(SetupFlipNeighborhood):
        def sample(self, sol, k, rng):
            return [(99, 99)] * k

    good = validate_component(COMPONENT_SETUP_FLIP, GoodSample(ctx.problem), ctx)
    assert "neighborhood.sample" not in {c.name for c in good.failures()}
    bad = validate_component(COMPONENT_SETUP_FLIP, BadSample(ctx.problem), ctx)
    assert bad.failed_layer == "contractual" and any(c.name == "neighborhood.sample" for c in bad.failures())


def test_ls_sample_is_a_skeleton_param_with_explicit_default():
    from core.assembler import SKELETONS
    from core.component import ComponentSpec

    for sk in ("ILS", "VNS"):
        spec = SKELETONS[sk].params["ls_sample"]
        assert ComponentSpec("_", "stop", (), (), {"ls_sample": spec}, None).default_params() == {"ls_sample": 32}
