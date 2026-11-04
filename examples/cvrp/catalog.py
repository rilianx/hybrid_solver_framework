"""Catálogo de referencia del CVRP (`HANDWRITTEN`); el registro es genérico (`core.catalog`)."""

from __future__ import annotations


from .components import (
    RadialRemoval,
    RandomRemoval,
    RelocateKick,
    RelocateNeighborhood,
    SingletonRoutes,
    TwoOptNeighborhood,
)
from .construction import CheapestInsertion, NearestFromDepot

CONSTRUCTOR_SKELETONS = ["SA", "ILS", "TS", "VNS", "HYB"]
LOCAL_SEARCH_SKELETONS = ["SA", "ILS", "TS", "VNS", "HYB"]

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
    ({"name": "relocate_kick", "slot": "perturbation", "compatible_skeletons": ["ILS", "HYB"], "params": {}},
     lambda problem: RelocateKick(problem)),
    ({"name": "random_removal", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}},
     lambda problem: RandomRemoval(problem)),
    ({"name": "radial_removal", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}},
     lambda problem: RadialRemoval(problem)),
]
