"""Catálogo de referencia del CVRP (`HANDWRITTEN`). Registrar, envolver puntajes y cargar
generados es genérico (`llm.catalog`); aquí solo se ata al pack del CVRP."""

from __future__ import annotations

from pathlib import Path

from core.component import ComponentRegistry
from core.fixing_policies import SlidingWindowPolicy
from llm import catalog as _catalog
from llm.generator import GeneratedComponent

from .components import (
    RadialRemoval,
    RandomRemoval,
    RelocateKick,
    RelocateNeighborhood,
    SingletonRoutes,
    TwoOptNeighborhood,
)
from .construction import CheapestInsertion, NearestFromDepot

CONSTRUCTOR_SKELETONS = ["SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH"]
LOCAL_SEARCH_SKELETONS = ["SA", "ILS", "TS", "VNS", "GRASP"]

HANDWRITTEN = [
    ({"name": "singleton_routes", "slot": "constructor", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: SingletonRoutes()),
    ({"name": "cheapest_insertion", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: CheapestInsertion(problem)),
    ({"name": "nearest_from_depot", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: NearestFromDepot(problem)),
    ({"name": "relocate", "slot": "neighborhood", "compatible_skeletons": LOCAL_SEARCH_SKELETONS, "params": {}},
     lambda problem: RelocateNeighborhood(problem)),
    ({"name": "two_opt", "slot": "neighborhood", "compatible_skeletons": LOCAL_SEARCH_SKELETONS, "params": {}},
     lambda problem: TwoOptNeighborhood(problem)),
    ({"name": "relocate_kick", "slot": "perturbation", "compatible_skeletons": ["ILS"], "params": {}},
     lambda problem: RelocateKick(problem)),
    ({"name": "random_removal", "slot": "destruction", "compatible_skeletons": ["LNS_MIP"], "params": {}},
     lambda problem: RandomRemoval(problem)),
    ({"name": "radial_removal", "slot": "destruction", "compatible_skeletons": ["LNS_MIP"], "params": {}},
     lambda problem: RadialRemoval(problem)),
    ({"name": "sliding_window", "slot": "fixing_policy", "compatible_skeletons": ["FIX_OPT"],
      "params": {"window_size": {"type": "int", "range": [1, 4]}, "overlap": {"type": "int", "range": [0, 2]}}},
     lambda problem, window_size=2, overlap=1: SlidingWindowPolicy(window_size, min(overlap, window_size - 1))),
]


def build_registry(generated: list[GeneratedComponent] | None = None, handwritten: bool = True,
                   exclude_slots: set[str] | None = None) -> ComponentRegistry:
    from .pack import PACK

    return _catalog.build_registry(PACK, generated, handwritten, exclude_slots)


def load_generated(workspace: str | Path = "generated/cvrp", revalidate: bool = True, verbose: bool = True,
                   combination: bool = True) -> list[GeneratedComponent]:
    from .pack import PACK

    return _catalog.load_generated(PACK, workspace, revalidate, verbose, combination)
