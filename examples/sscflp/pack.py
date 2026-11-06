"""`ProblemPack` del SSCFLP. Lo humano es la instancia, la descripción para el LLM, los casos de prueba y el oráculo en
Python (`model_parts`); el modelo C++, los componentes y la vista MIP los escribe el LLM (`native_parts.GENERATION`)."""

from __future__ import annotations

from random import Random

from core.packs import TrivialConstructor, parts_pack
from core.problem_pack import ProblemPack

from . import model_parts
from .instance import SSCFLPInstance
from .llm_spec import make_model_spec

SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]


def _feasible(inst: SSCFLPInstance) -> bool:
    try:
        model_parts.trivial_solution(inst)
        return True
    except ValueError:
        return False


def make_instances(n: int, seed0: int, size: dict):
    """Como las de Holmberg (`SSCFLPInstance.random`), con holgura de capacidad al azar entre 1.5 y 4 (1.3 en las
    micro-instancias, para que la capacidad decida); se descartan las que la trivial no resuelve."""
    out = []
    for k in range(n):
        rng = Random(seed0 + k)
        ratio = 1.3 if size["customers"] <= 10 else None
        inst = SSCFLPInstance.random(size["facilities"], size["customers"], rng, ratio=ratio)
        while not _feasible(inst):
            inst = SSCFLPInstance.random(size["facilities"], size["customers"], rng, ratio=ratio)
        out.append(inst)
    return out


def parse_size(text: str) -> dict:
    """`<centros>x<clientes>`, p.ej. `30x200`."""
    n, m = text.lower().split("x")
    return {"facilities": int(n), "customers": int(m)}


def _load_cases():
    from .cases import load_cases

    return load_cases()


_BASE = ProblemPack(
    name="sscflp", module="examples.sscflp", problem_factory=None,
    make_instances=make_instances, parse_size=parse_size, default_size="20x100", baseline_constructor=None,
    load_instance=SSCFLPInstance.load, make_model_spec=make_model_spec, micro_size="4x10", load_cases=_load_cases,
    constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.sscflp.model_parts", make_model_spec(), "sscflp")
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.sscflp.native_parts"
PACK.bench_size = "30x200"
PACK.variants = {"assignment": (make_model_spec, "examples.sscflp.model_parts")}
