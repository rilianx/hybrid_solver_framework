"""Catálogo de componentes del CLSP: los escritos a mano (`HANDWRITTEN`, con las políticas
de fijación del núcleo). Registrar, envolver puntajes y cargar generados es genérico
(`llm.catalog`); aquí solo se ata al pack del CLSP.
"""

from __future__ import annotations

from pathlib import Path

from core.component import ComponentRegistry, ComponentSpec
from core.fixing_policies import SlidingWindowPolicy
from llm import catalog as _catalog
from llm.generator import GeneratedComponent

from .construction import LatestSource, UnitMarginalCost
from .components import (
    LotForLotConstructor,
    PeriodWindowDestruction,
    RandomSetupDestruction,
    SetupFlipNeighborhood,
    SetupFlipPerturbation,
)

CONSTRUCTOR_SKELETONS = ["SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH", "MIP_PERTURB"]

HANDWRITTEN = [
    (
        {"name": "lot_for_lot", "slot": "constructor", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
        lambda problem: LotForLotConstructor(),
    ),
    (
        {"name": "unit_marginal_cost", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
        lambda problem: UnitMarginalCost(problem),
    ),
    (
        {"name": "latest_source", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
        lambda problem: LatestSource(problem),
    ),
    (
        {"name": "setup_flip", "slot": "neighborhood", "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"], "params": {}},
        lambda problem: SetupFlipNeighborhood(problem),
    ),
    (
        {"name": "setup_flip_perturbation", "slot": "perturbation", "compatible_skeletons": ["ILS"], "params": {}},
        lambda problem: SetupFlipPerturbation(),
    ),
    (
        {"name": "period_window", "slot": "destruction", "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"], "params": {}},
        lambda problem: PeriodWindowDestruction(problem.inst),
    ),
    (
        {"name": "random_setups", "slot": "destruction", "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"], "params": {}},
        lambda problem: RandomSetupDestruction(problem.inst),
    ),
    (
        {
            "name": "sliding_window",
            "slot": "fixing_policy",
            "compatible_skeletons": ["FIX_OPT"],
            "params": {"window_size": {"type": "int", "range": [1, 4]}, "overlap": {"type": "int", "range": [0, 2]}},
        },
        lambda problem, window_size=2, overlap=1: SlidingWindowPolicy(window_size, min(overlap, window_size - 1)),
    ),
]


def build_registry(generated: list[GeneratedComponent] | None = None, handwritten: bool = True,
                   exclude_slots: set[str] | None = None) -> ComponentRegistry:
    """Ver `llm.catalog.build_registry`."""
    from .pack import PACK

    return _catalog.build_registry(PACK, generated, handwritten, exclude_slots)


def greedy_constructor_spec(score_spec: ComponentSpec) -> ComponentSpec:
    return _catalog.greedy_constructor_spec(score_spec, CONSTRUCTOR_SKELETONS)


def load_generated(workspace: str | Path = "generated/clsp", revalidate: bool = True, verbose: bool = True,
                   combination: bool = True) -> list[GeneratedComponent]:
    """Ver `llm.catalog.load_generated`."""
    from .pack import PACK

    return _catalog.load_generated(PACK, workspace, revalidate, verbose, combination)
