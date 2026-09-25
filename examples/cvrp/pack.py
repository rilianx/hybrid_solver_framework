"""`ProblemPack` del CVRP: lo que el framework recibe de este problema (ver `core.problem_pack`)."""

from __future__ import annotations

from random import Random

from core.problem_pack import ProblemPack

from .catalog import CONSTRUCTOR_SKELETONS, HANDWRITTEN
from .components import SingletonRoutes
from .llm_spec import make_contexts, make_spec
from .problem_model import CVRPInstance, CVRPModel


def make_instances(n: int, seed0: int, size: dict):
    """Mitad uniformes y mitad agrupadas, rutas de ~5 clientes."""
    return [CVRPInstance.random(size["customers"], Random(seed0 + k), clustered=k % 2 == 1) for k in range(n)]


def parse_size(text: str) -> dict:
    return {"customers": int(text)}


PACK = ProblemPack(
    name="cvrp",
    module="examples.cvrp",
    problem_factory=CVRPModel,
    handwritten=HANDWRITTEN,
    make_spec=make_spec,
    make_contexts=make_contexts,
    make_instances=make_instances,
    parse_size=parse_size,
    default_size="30",
    baseline_constructor=SingletonRoutes,
    load_instance=CVRPInstance.load,
    constructor_skeletons=CONSTRUCTOR_SKELETONS,
)
