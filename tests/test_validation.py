"""Las capas de validación (§7) aceptan los componentes correctos de ambos
pilotos y rechazan, con mensaje concreto, componentes deliberadamente rotos
del tipo que un LLM produce (delta mal calculado, undo incorrecto, destrucción
que inventa variables, sub-MIP que ignora variables fijas, parada que nunca
llega, fuga de tiempo...)."""

from itertools import product
from random import Random

import pytest

pytest.importorskip("pulp")

from core.common_components import BetterAcceptance, MaxIterationsStop, MaxTimeStop, MIPModelRepair
from core.fixing_policies import SlidingWindowPolicy
from core.validation import (
    ValidationContext,
    validate_component,
    validate_problem_model,
    validate_variant,
)
from core.validation.syntactic import check_protocol
from examples.knapsack.components import (
    COMPONENT_BIT_FLIP_NEIGHBORHOOD,
    COMPONENT_GREEDY_RANDOMIZED_CONSTRUCTOR,
    COMPONENT_KNAPSACK_MIP_REPAIR,
    COMPONENT_RANDOM_DESTRUCTION,
    COMPONENT_RANDOM_FLIP_PERTURBATION,
    BitFlipNeighborhood,
    GreedyRandomizedConstructor,
    KnapsackMIPRepair,
    RandomDestruction,
    RandomFlipPerturbation,
)
from examples.knapsack.problem_model import KnapsackInstance, KnapsackModel, KnapsackObjective, bound_problem_model
from examples.lotsizing.components import (
    COMPONENT_PERIOD_WINDOW_DESTRUCTION,
    COMPONENT_SETUP_FLIP,
    LotForLotConstructor,
    PeriodWindowDestruction,
    SetupFlipNeighborhood,
)
from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel
from skeletons.lns_mip import build_lns_mip, run_lns_mip
from skeletons.sa import build_sa, make_run

# --------------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def knap_ctx():
    inst = KnapsackInstance.random(8, Random(5))
    problem = bound_problem_model(inst)
    evaluator = KnapsackObjective(KnapsackModel(), inst)
    return ValidationContext(
        problem=problem,
        instances=[inst],
        trivial_solutions=[tuple(False for _ in range(inst.n))],
        baseline_constructor=GreedyRandomizedConstructor(alpha=1.0),  # alpha=1 == puramente aleatorio
        reference_destruction=RandomDestruction(),
        reference_neighborhood=BitFlipNeighborhood(evaluator),
        enumerate_solutions=lambda inst: list(product([False, True], repeat=inst.n)),
    ), evaluator


@pytest.fixture(scope="module")
def clsp_ctx():
    inst = CLSPInstance.random(3, 4, Random(2))
    problem = LotSizingModel(inst)
    return ValidationContext(
        problem=problem,
        instances=[inst],
        trivial_solutions=[LotForLotConstructor().build(inst, Random(0))],
        baseline_constructor=LotForLotConstructor(),
        reference_destruction=PeriodWindowDestruction(inst),
        mip_time_limit=5.0,
    )


# --------------------------------------------------------------------------- componentes correctos


def test_good_knapsack_components_pass(knap_ctx):
    ctx, evaluator = knap_ctx
    cases = [
        (COMPONENT_GREEDY_RANDOMIZED_CONSTRUCTOR, GreedyRandomizedConstructor(0.3)),
        (COMPONENT_BIT_FLIP_NEIGHBORHOOD, BitFlipNeighborhood(evaluator)),
        (COMPONENT_RANDOM_FLIP_PERTURBATION, RandomFlipPerturbation()),
        (COMPONENT_RANDOM_DESTRUCTION, RandomDestruction()),
        (COMPONENT_KNAPSACK_MIP_REPAIR, KnapsackMIPRepair()),
    ]
    for comp, impl in cases:
        report = validate_component(comp, impl, ctx)
        assert report.passed, report.feedback()


def test_good_clsp_components_pass(clsp_ctx):
    for comp, impl in [
        (COMPONENT_SETUP_FLIP, SetupFlipNeighborhood(clsp_ctx.problem)),
        (COMPONENT_PERIOD_WINDOW_DESTRUCTION, PeriodWindowDestruction(clsp_ctx.instances[0])),
        ({"name": "rf_policy", "slot": "fixing_policy"}, SlidingWindowPolicy(2, 1)),
        ({"name": "stop_iters", "slot": "stop"}, MaxIterationsStop(10)),
        ({"name": "better", "slot": "acceptance"}, BetterAcceptance()),
        ({"name": "mip_repair", "slot": "repair_mip"}, MIPModelRepair(clsp_ctx.problem)),
    ]:
        report = validate_component(comp, impl, clsp_ctx)
        assert report.passed, report.feedback()


def test_problem_models_pass_semantic_layer(knap_ctx, clsp_ctx):
    ctx, _ = knap_ctx
    r = validate_problem_model(ctx)
    assert r.passed, r.feedback()
    assert any(c.name == "full_mip_matches_brute_force" for c in r.results)
    r2 = validate_problem_model(clsp_ctx)
    assert r2.passed, r2.feedback()


# --------------------------------------------------------------------------- componentes rotos


def test_syntactic_layer_detects_missing_methods(knap_ctx):
    class HalfNeighborhood:
        def moves(self, sol):
            return []

    r = check_protocol("neighborhood", HalfNeighborhood())
    assert not r.passed and "apply" in r.message and "delta" in r.message


def test_syntactic_layer_rejects_bad_component_dict(knap_ctx):
    ctx, _ = knap_ctx
    report = validate_component({"name": "x", "slot": "no_such_slot"}, object(), ctx)
    assert report.failed_layer == "syntactic"


def test_contractual_detects_wrong_delta(knap_ctx):
    ctx, evaluator = knap_ctx

    class WrongDelta(BitFlipNeighborhood):
        def delta(self, sol, m):
            return super().delta(sol, m) * 0.5  # error típico: delta a medias

    report = validate_component(COMPONENT_BIT_FLIP_NEIGHBORHOOD, WrongDelta(evaluator), ctx)
    assert report.failed_layer == "contractual"
    assert any(c.name == "neighborhood.delta_consistent" for c in report.failures())


def test_contractual_detects_wrong_undo(knap_ctx):
    ctx, evaluator = knap_ctx

    class WrongUndo(BitFlipNeighborhood):
        def undo(self, sol, m):
            return sol  # no deshace nada

    report = validate_component(COMPONENT_BIT_FLIP_NEIGHBORHOOD, WrongUndo(evaluator), ctx)
    assert any(c.name == "neighborhood.undo_apply_identity" for c in report.failures())


def test_contractual_detects_destruction_leaking_unknown_variables(knap_ctx):
    ctx, _ = knap_ctx

    class LeakyDestruction(RandomDestruction):
        def destroy(self, sol, ratio, rng):
            partial, free = super().destroy(sol, ratio, rng)
            free.add("x999")
            return partial, free

    report = validate_component(COMPONENT_RANDOM_DESTRUCTION, LeakyDestruction(), ctx)
    assert any(c.name == "destruction.free_subset_of_variables" for c in report.failures())
    assert "x999" in report.feedback()


def test_contractual_detects_repair_ignoring_fixed_vars(knap_ctx):
    ctx, _ = knap_ctx

    class IgnoresFixed(KnapsackMIPRepair):
        def repair_mip(self, model, fixed, free_vars, time_limit, warm_start=None):
            return super().repair_mip(model, {}, set(model.variables()), time_limit, warm_start)

    report = validate_component(COMPONENT_KNAPSACK_MIP_REPAIR, IgnoresFixed(), ctx)
    assert any(c.name == "repair_mip.respects_fixed" for c in report.failures())


def test_contractual_detects_infeasible_constructor(knap_ctx):
    ctx, _ = knap_ctx

    class TakeAll:
        def build(self, inst, rng):
            return tuple(True for _ in range(inst.n))

    report = validate_component(COMPONENT_GREEDY_RANDOMIZED_CONSTRUCTOR, TakeAll(), ctx)
    assert any(c.name == "constructor.feasible" for c in report.failures())


def test_contractual_detects_stop_that_never_triggers(knap_ctx):
    ctx, _ = knap_ctx

    class Never:
        def stop(self, state):
            return False

    report = validate_component({"name": "never", "slot": "stop"}, Never(), ctx)
    assert any(c.name == "stop.eventually_true" for c in report.failures())


def test_contractual_detects_policy_not_covering_all(knap_ctx):
    ctx, _ = knap_ctx

    class Partial(SlidingWindowPolicy):
        def schedule(self, groups, params=None):
            steps = list(super().schedule(groups, params))
            yield steps[0]  # se queda corto

    class Groups:  # el knapsack tiene un solo grupo; partimos artificialmente en dos
        pass

    ctx2 = ValidationContext(problem=_TwoGroups(ctx.problem), instances=ctx.instances, trivial_solutions=ctx.trivial_solutions)
    report = validate_component({"name": "partial", "slot": "fixing_policy"}, Partial(1, 0), ctx2)
    assert any(c.name == "fixing_policy.covers_all" for c in report.failures())


class _TwoGroups:
    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def variable_groups(self, inst):
        names = [f"x{i}" for i in range(inst.n)]
        half = len(names) // 2
        return {"a": names[:half], "b": names[half:]}


def test_semantic_layer_detects_objective_disagreement(knap_ctx):
    ctx, _ = knap_ctx

    class ScaledObjective:
        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def objective(self, sol):
            return 2.0 * self._inner.objective(sol) - 1.0  # evaluador heurístico mal escalado

    bad_ctx = ValidationContext(problem=ScaledObjective(ctx.problem), instances=ctx.instances, trivial_solutions=ctx.trivial_solutions)
    report = validate_problem_model(bad_ctx)
    assert any(c.name == "objective_agreement" for c in report.failures()), report.feedback()


# --------------------------------------------------------------------------- variantes


def _sa_runner(ctx, evaluator):
    def run(inst, rng, budget):
        sk, extra = build_sa(ctx.problem, GreedyRandomizedConstructor(1.0), BitFlipNeighborhood(evaluator), MaxTimeStop(budget), T0=5.0, alpha=0.99)
        return make_run(sk, extra)(inst, rng)

    return run


def test_operational_and_quality_pass_for_sa_variant(knap_ctx):
    ctx, evaluator = knap_ctx
    report = validate_variant(_sa_runner(ctx, evaluator), ctx, name="SA/knapsack", budget_seconds=0.5)
    assert report.passed, report.feedback()


def test_operational_detects_time_leak(knap_ctx):
    ctx, evaluator = knap_ctx

    class SlowNeighborhood(BitFlipNeighborhood):
        def moves(self, sol):
            import time

            time.sleep(3.0)  # una iteración tarda más que todo el presupuesto
            return super().moves(sol)

    def run(inst, rng, budget):
        sk, extra = build_sa(ctx.problem, GreedyRandomizedConstructor(1.0), SlowNeighborhood(evaluator), MaxTimeStop(budget))
        return make_run(sk, extra)(inst, rng)

    report = validate_variant(run, ctx, budget_seconds=0.5)
    assert report.failed_layer == "operational"
    assert any(c.name == "respects_time_budget" for c in report.failures())


def test_operational_detects_exceptions(knap_ctx):
    ctx, evaluator = knap_ctx

    class Boom(BitFlipNeighborhood):
        def apply(self, sol, m):
            raise KeyError("índice inventado")

    def run(inst, rng, budget):
        sk, extra = build_sa(ctx.problem, GreedyRandomizedConstructor(1.0), Boom(evaluator), MaxTimeStop(budget))
        return make_run(sk, extra)(inst, rng)

    report = validate_variant(run, ctx, budget_seconds=0.5)
    assert any(c.name == "no_exceptions" and "KeyError" in c.message for c in report.failures())


def test_quality_detects_inert_variant(knap_ctx):
    ctx, evaluator = knap_ctx

    class NoMoves(BitFlipNeighborhood):
        def moves(self, sol):
            return []  # nunca propone nada: variante inerte

    def run(inst, rng, budget):
        sk, extra = build_sa(ctx.problem, GreedyRandomizedConstructor(1.0), NoMoves(evaluator), MaxTimeStop(budget))
        return make_run(sk, extra)(inst, rng)

    report = validate_variant(run, ctx, budget_seconds=0.3)
    assert report.failed_layer == "quality"
    assert any(c.name == "not_inert" for c in report.failures())


def test_lns_mip_variant_passes_on_clsp(clsp_ctx):
    def run(inst, rng, budget):
        sk = build_lns_mip(clsp_ctx.problem, LotForLotConstructor(), PeriodWindowDestruction(inst), MIPModelRepair(clsp_ctx.problem),
                           BetterAcceptance(), MaxTimeStop(budget), destroy_ratio=0.5, mip_time_limit=1.0)
        return run_lns_mip(sk, inst, rng, 0.5)

    report = validate_variant(run, clsp_ctx, name="LNS-MIP/CLSP", budget_seconds=2.0)
    assert report.passed, report.feedback()
