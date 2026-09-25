"""`ProblemPack` del CLSP: lo que el framework recibe de este problema (ver `core.problem_pack`)."""

from __future__ import annotations

from random import Random

from core.problem_pack import ProblemPack

from .catalog import CONSTRUCTOR_SKELETONS, HANDWRITTEN
from .components import LotForLotConstructor
from .llm_spec import make_contexts, make_spec
from .problem_model import CLSPInstance, LotSizingModel


def make_instances(n: int, seed0: int, size: dict, utilization: float = 0.95, tbo: float = 3.0):
    return [CLSPInstance.trigeiro(size["items"], size["periods"], Random(seed0 + k), utilization=utilization, tbo=tbo)
            for k in range(n)]


def parse_size(text: str) -> dict:
    items, periods = text.lower().split("x")
    return {"items": int(items), "periods": int(periods)}


PACK = ProblemPack(
    name="clsp",
    module="examples.lotsizing",
    problem_factory=LotSizingModel,
    handwritten=HANDWRITTEN,
    make_spec=make_spec,
    make_contexts=make_contexts,
    make_instances=make_instances,
    parse_size=parse_size,
    default_size="10x15",
    baseline_constructor=LotForLotConstructor,
    load_instance=CLSPInstance.load,
    constructor_skeletons=CONSTRUCTOR_SKELETONS,
)
