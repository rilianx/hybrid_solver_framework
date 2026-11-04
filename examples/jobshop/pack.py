"""`ProblemPack` del job shop (makespan). Lo humano es la instancia, la descripción para el LLM, los casos de prueba y
el modelo de referencia en Python (`model_parts`, oráculo y vista MIP); el modelo C++ y los componentes los escribe el
LLM (`native_parts.GENERATION`)."""

from __future__ import annotations

from random import Random

from core.packs import TrivialConstructor, parts_pack
from core.problem_pack import ProblemPack

from . import model_parts
from .instance import JSSPInstance
from .llm_spec import make_model_spec

SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]


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
    name="jobshop", module="examples.jobshop", problem_factory=None, handwritten=[],
    make_instances=make_instances, parse_size=parse_size, default_size="10x10", baseline_constructor=None,
    load_instance=JSSPInstance.load, make_model_spec=make_model_spec, micro_size="4x3", load_cases=_load_cases,
    constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.jobshop.model_parts", make_model_spec(), "jobshop")
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.jobshop.native_parts"
PACK.bench_size = "20x15"
PACK.variants = {"sequences": (make_model_spec, "examples.jobshop.model_parts")}
