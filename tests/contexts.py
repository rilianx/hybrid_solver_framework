"""Micro-contextos de validación sobre los modelos Python escritos a mano del CLSP y del CVRP, para probar las capas
de validación (`core.validation`) con componentes conocidos. La generación nativa usa los de `core.packs.parts_contexts`."""

from __future__ import annotations

from random import Random

from core.assembler import Assembler
from core.catalog import build_registry
from core.component import ComponentSpec
from core.construction import GreedyConstructor
from core.validation import ValidationContext
from core.validation.base import DiversityProbe
from core.validation.combination import CombinationProbe


def _assembler_for(pack, problem_factory):
    def assembler_for(slot, components):
        registry = build_registry(pack, exclude_slots={slot})  # sin los de mano de ESTE slot
        names = []
        for component, factory in components:
            spec = dict(component)
            spec.pop("combination_gains", None)
            registry.register(ComponentSpec.from_dict(spec, factory))
            names.append(spec["name"])
        assembler = Assembler(problem_factory=problem_factory, registry=registry)
        assembler.probe_component = names[0]
        return assembler

    return assembler_for


# ------------------------------------------------------------------------------------------------------------ CLSP
def clsp_feasible_trivial(problem, inst):
    """Partida factible: lot-for-lot si lo es; si no, el greedy de costo marginal (lot-for-lot deja faltante cuando
    los tiempos de setup de todos los ítems exceden la capacidad del pico)."""
    from examples.lotsizing.components import LotForLotConstructor
    from examples.lotsizing.construction import UnitMarginalCost

    sol = LotForLotConstructor().build(inst, Random(0))
    if problem.is_feasible(sol):
        return sol
    sol = GreedyConstructor(problem, UnitMarginalCost(problem)).build(inst, Random(0))
    return sol if problem.is_feasible(sol) else None


def clsp_diversity_probe(n_items: int = 10, n_periods: int = 15, seed: int = 100) -> DiversityProbe | None:
    """Instancia de tamaño realista donde se mide si dos componentes son el mismo operador con otro nombre."""
    from examples.lotsizing import problem_model as pm

    inst = pm.CLSPInstance.trigeiro(n_items, n_periods, Random(seed), utilization=0.95, tbo=3.0)
    problem = pm.LotSizingModel(inst)
    sol = clsp_feasible_trivial(problem, inst)
    return None if sol is None else DiversityProbe(problem=problem, solution=sol, max_similarity=0.8)


def clsp_combination_probe(probe: DiversityProbe | None, budget: float = 1.0):
    from examples.lotsizing import problem_model as pm
    from examples.lotsizing.pack import PACK

    if probe is None:
        return None
    return CombinationProbe(instance=probe.problem.inst, assembler_for=_assembler_for(PACK, pm.LotSizingModel),
                            starts=["lot_for_lot", "greedy_unit_marginal_cost"], budget=budget)


def clsp_contexts(n_contexts: int = 2, n_items: int = 3, n_periods: int = 5, seed: int = 7, strict: bool = True,
                  reference_free: bool = False, combination: bool = False) -> list[ValidationContext]:
    """`strict`: un vecindario tiene que mejorar desde la partida; `reference_free`: sin vecindario de referencia
    para el feedback."""
    from examples.lotsizing import problem_model as pm
    from examples.lotsizing.components import LotForLotConstructor, PeriodWindowDestruction, SetupFlipNeighborhood

    probe = clsp_diversity_probe()
    combo = clsp_combination_probe(probe) if combination else None
    contexts = []
    k, retry = 0, 0
    while len(contexts) < n_contexts and retry < 10:
        rng = Random(seed + k + 1000 * retry)
        if k % 2 == 0:
            inst = pm.CLSPInstance.trigeiro(n_items, n_periods, rng, utilization=0.95, tbo=2.0)
        else:
            inst = pm.CLSPInstance.random(n_items, n_periods, rng)
        problem = pm.LotSizingModel(inst)
        trivial = clsp_feasible_trivial(problem, inst)
        if trivial is None:
            retry += 1
            continue
        k, retry = k + 1, 0
        contexts.append(ValidationContext(
            problem=problem, instances=[inst], trivial_solutions=[trivial],
            baseline_constructor=LotForLotConstructor(),
            reference_destruction=PeriodWindowDestruction(inst),
            reference_neighborhood=None if reference_free else SetupFlipNeighborhood(problem),
            mip_time_limit=5.0, max_moves_checked=30, require_improving_from_start=strict,
            diversity_probe=probe, combination=combo,
        ))
    return contexts


# ------------------------------------------------------------------------------------------------------------ CVRP
def _cvrp_greedy(problem):
    from examples.cvrp.construction import CheapestInsertion

    return GreedyConstructor(problem, CheapestInsertion(problem))


def cvrp_contexts(n_contexts: int = 2, n_customers: int = 6, seed: int = 7, strict: bool = True,
                  reference_free: bool = False, combination: bool = False) -> list[ValidationContext]:
    from examples.cvrp import problem_model as pm
    from examples.cvrp.components import RandomRemoval, RelocateNeighborhood, SingletonRoutes
    from examples.cvrp.pack import PACK

    inst = pm.CVRPInstance.random(30, Random(100))
    problem = pm.CVRPModel(inst)
    probe = DiversityProbe(problem=problem, solution=_cvrp_greedy(problem).build(inst, Random(0)), max_similarity=0.8)
    combo = (CombinationProbe(instance=inst, assembler_for=_assembler_for(PACK, pm.CVRPModel),
                              starts=["singleton_routes", "greedy_cheapest_insertion"], budget=1.0)
             if combination else None)
    contexts = []
    for k in range(n_contexts):
        inst = pm.CVRPInstance.random(n_customers, Random(seed + k), route_size=3.0, clustered=k % 2 == 1)
        problem = pm.CVRPModel(inst)
        contexts.append(ValidationContext(
            problem=problem, instances=[inst], trivial_solutions=[SingletonRoutes().build(inst, Random(0))],
            baseline_constructor=_cvrp_greedy(problem),
            reference_destruction=RandomRemoval(problem),
            reference_neighborhood=None if reference_free else RelocateNeighborhood(problem),
            mip_time_limit=10.0, max_moves_checked=30, require_improving_from_start=strict,
            diversity_probe=probe, combination=combo,
        ))
    return contexts
