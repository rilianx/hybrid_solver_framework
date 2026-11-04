"""`ProblemPack` del flow shop de permutación con flowtime total: el primer problema que entra al framework sin modelo ni
componentes escritos a mano. Lo humano es la instancia (formato de Taillard), la descripción para el LLM, los casos de
prueba y un modelo de referencia en Python que hace de oráculo (`model_parts`); el modelo C++ y los componentes los
escribe el LLM (`native_parts.GENERATION`)."""

from __future__ import annotations

from random import Random

from core.problem_pack import ProblemPack
from core.packs import TrivialConstructor, parts_pack

from . import model_parts
from .instance import PFSPInstance
from .llm_spec import make_model_spec

SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]


def parse_size(text: str) -> dict:
    """`50x10` = 50 trabajos, 10 máquinas."""
    n, _, m = text.lower().partition("x")
    return {"jobs": int(n), "machines": int(m or 5)}


def make_instances(n: int, seed0: int, size: dict):
    return [PFSPInstance.random(size["jobs"], size["machines"], Random(seed0 + k)) for k in range(n)]


def _load_cases():
    from .cases import load_cases

    return load_cases()


_BASE = ProblemPack(
    name="flowshop", module="examples.flowshop", problem_factory=None, handwritten=[],
    make_instances=make_instances, parse_size=parse_size, default_size="50x10", baseline_constructor=None,
    load_instance=PFSPInstance.load, make_model_spec=make_model_spec, micro_size="6x3", load_cases=_load_cases,
    constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.flowshop.model_parts", make_model_spec(), "flowshop")
PACK.module = "examples.flowshop"
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.flowshop.native_parts"
PACK.bench_size = "100x10"
# tiempo proporcional a n·m como en la literatura (n·m/2·t ms); 1 en el tamaño por defecto (50x10)
PACK.budget_scale = lambda inst: inst.n_jobs * inst.n_machines / 500
PACK.variants = {"permutation": (make_model_spec, "examples.flowshop.model_parts")}
