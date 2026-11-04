"""Catálogo de componentes del CLSP escritos a mano (`HANDWRITTEN`); el registro es genérico (`core.catalog`)."""

from __future__ import annotations


from .construction import LatestSource, UnitMarginalCost
from .components import (
    LotForLotConstructor,
    PeriodWindowDestruction,
    RandomSetupDestruction,
    SetupFlipNeighborhood,
    SetupFlipPerturbation,
)

CONSTRUCTOR_SKELETONS = ["SA", "ILS", "TS", "VNS", "HYB"]

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
        {"name": "setup_flip", "slot": "neighborhood", "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "HYB"], "params": {}},
        lambda problem: SetupFlipNeighborhood(problem),
    ),
    (
        {"name": "setup_flip_perturbation", "slot": "perturbation", "compatible_skeletons": ["ILS", "HYB"], "params": {}},
        lambda problem: SetupFlipPerturbation(),
    ),
    (
        {"name": "period_window", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}},
        lambda problem: PeriodWindowDestruction(problem.inst),
    ),
    (
        {"name": "random_setups", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}},
        lambda problem: RandomSetupDestruction(problem.inst),
    ),
]
