"""Micro-contextos de validación sobre el CLSP (modelo por piezas de referencia y los componentes de
`tests/clsp_fixtures.py`), para probar las capas de validación (`core.validation`) con componentes conocidos. La
generación nativa usa los de `core.packs.parts_contexts`."""

from __future__ import annotations

from random import Random

from core.assembler import Assembler
from core.component import ComponentSpec
from core.construction import GreedyConstructor
from core.validation import ValidationContext
from core.validation.base import DiversityProbe
from core.validation.combination import CombinationProbe


def _assembler_for(problem_factory):
    from tests.clsp_fixtures import clsp_registry

    def assembler_for(slot, components):
        registry = clsp_registry(exclude_slots={slot})  # sin los de mano de ESTE slot
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
    from tests.clsp_fixtures import LotForLotConstructor, UnitMarginalCost

    sol = LotForLotConstructor().build(inst, Random(0))
    if problem.is_feasible(sol):
        return sol
    sol = GreedyConstructor(problem, UnitMarginalCost(problem)).build(inst, Random(0))
    return sol if problem.is_feasible(sol) else None


def clsp_diversity_probe(n_items: int = 10, n_periods: int = 15, seed: int = 100) -> DiversityProbe | None:
    """Instancia de tamaño realista donde se mide si dos componentes son el mismo operador con otro nombre."""
    from examples.lotsizing.instance import CLSPInstance
    from tests.clsp_fixtures import LotSizingModel

    inst = CLSPInstance.trigeiro(n_items, n_periods, Random(seed), utilization=0.95, tbo=3.0)
    problem = LotSizingModel(inst)
    sol = clsp_feasible_trivial(problem, inst)
    return None if sol is None else DiversityProbe(problem=problem, solution=sol, max_similarity=0.8)


def clsp_combination_probe(probe: DiversityProbe | None, budget: float = 1.0):
    from tests.clsp_fixtures import LotSizingModel

    if probe is None:
        return None
    return CombinationProbe(instance=probe.problem.inst, assembler_for=_assembler_for(LotSizingModel),
                            starts=["lot_for_lot", "greedy_unit_marginal_cost"], budget=budget)


def clsp_contexts(n_contexts: int = 2, n_items: int = 3, n_periods: int = 5, seed: int = 7, strict: bool = True,
                  reference_free: bool = False, combination: bool = False) -> list[ValidationContext]:
    """`strict`: un vecindario tiene que mejorar desde la partida; `reference_free`: sin vecindario de referencia
    para el feedback."""
    from core.packs import GroupWindowDestruction
    from examples.lotsizing.instance import CLSPInstance
    from tests.clsp_fixtures import LotForLotConstructor, LotSizingModel, SetupFlipNeighborhood

    probe = clsp_diversity_probe()
    combo = clsp_combination_probe(probe) if combination else None
    contexts = []
    k, retry = 0, 0
    while len(contexts) < n_contexts and retry < 10:
        rng = Random(seed + k + 1000 * retry)
        if k % 2 == 0:
            inst = CLSPInstance.trigeiro(n_items, n_periods, rng, utilization=0.95, tbo=2.0)
        else:
            inst = CLSPInstance.random(n_items, n_periods, rng)
        problem = LotSizingModel(inst)
        trivial = clsp_feasible_trivial(problem, inst)
        if trivial is None:
            retry += 1
            continue
        k, retry = k + 1, 0
        contexts.append(ValidationContext(
            problem=problem, instances=[inst], trivial_solutions=[trivial],
            baseline_constructor=LotForLotConstructor(),
            reference_destruction=GroupWindowDestruction(problem),
            reference_neighborhood=None if reference_free else SetupFlipNeighborhood(problem),
            mip_time_limit=5.0, max_moves_checked=30, require_improving_from_start=strict,
            diversity_probe=probe, combination=combo,
        ))
    return contexts
