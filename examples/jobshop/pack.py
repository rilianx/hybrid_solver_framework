"""`ProblemPack` del job shop (makespan): lo que el framework recibe de este problema.

Es el primer problema que entra directamente por piezas: el `ProblemModel` del pack base es el de
las piezas de referencia por secuencias (`model_parts`), armado con `llm.cycle.parts_pack`, más el
catálogo escrito a mano (`catalog.HANDWRITTEN`). Las variantes del ciclo completo son `sequences`
(la misma representación) y `operations` (permutación con repetición, `ops_parts`).
"""

from __future__ import annotations

from random import Random

from core.problem_pack import ProblemPack
from llm.cycle import parts_pack

from . import model_parts
from .catalog import CONSTRUCTOR_SKELETONS, HANDWRITTEN
from .components import JobOrder
from .instance import JSSPInstance
from .llm_spec import make_model_spec, make_ops_model_spec


def parse_size(text: str) -> dict:
    """`10x10` = 10 trabajos, 10 máquinas (`10` = cuadrada)."""
    n, _, m = text.lower().partition("x")
    return {"jobs": int(n), "machines": int(m or n)}


def make_instances(n: int, seed0: int, size: dict):
    return [JSSPInstance.random(size["jobs"], size["machines"], Random(seed0 + k)) for k in range(n)]


def _load_cases():
    from .cases import load_cases

    return load_cases()


_BASE = ProblemPack(
    name="jobshop",
    module="examples.jobshop",
    problem_factory=None,
    handwritten=[],
    make_spec=None,
    make_contexts=None,
    make_instances=make_instances,
    parse_size=parse_size,
    default_size="10x10",
    baseline_constructor=JobOrder,
    load_instance=JSSPInstance.load,
    make_model_spec=make_model_spec,
    micro_size="4x3",
    load_cases=_load_cases,
    constructor_skeletons=CONSTRUCTOR_SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.jobshop.model_parts", make_model_spec(), "jobshop")
PACK.module = "examples.jobshop"
PACK.handwritten = HANDWRITTEN
PACK.baseline_constructor = JobOrder
PACK.variants = {"sequences": (make_model_spec, "examples.jobshop.model_parts"),
                 "operations": (make_ops_model_spec, "examples.jobshop.ops_parts")}
