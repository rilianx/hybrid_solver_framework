"""`ProblemPack` del CVRP (flota libre). Lo humano es la instancia, la descripción para el LLM, los casos de prueba y el
modelo de referencia en Python (`model_parts`, oráculo y vista MIP); el modelo C++ y los componentes los escribe el LLM
(`native_parts.GENERATION`)."""

from __future__ import annotations

from random import Random

from core.packs import TrivialConstructor, parts_pack
from core.problem_pack import ProblemPack

from . import model_parts
from .instance import CVRPInstance
from .llm_spec import make_model_spec

SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]


def make_instances(n: int, seed0: int, size: dict):
    """Mitad uniformes y mitad agrupadas; rutas de ~5 clientes (de ~3 en micro-instancias). Con un tamaño `x<n>`
    (p.ej. `x150`), como las instancias X de Uchoa (`CVRPInstance.uchoa_like`)."""
    if size.get("uchoa"):
        return [CVRPInstance.uchoa_like(size["customers"], Random(seed0 + k)) for k in range(n)]
    route = 3.0 if size["customers"] <= 8 else 5.0
    return [CVRPInstance.random(size["customers"], Random(seed0 + k), route_size=route, clustered=k % 2 == 1) for k in range(n)]


def _load_cases():
    from .cases import load_cases

    return load_cases()


def parse_size(text: str) -> dict:
    if text.startswith("x"):
        return {"customers": int(text[1:]), "uchoa": True}
    return {"customers": int(text)}


_BASE = ProblemPack(
    name="cvrp", module="examples.cvrp", problem_factory=None,
    make_instances=make_instances, parse_size=parse_size, default_size="30", baseline_constructor=None,
    load_instance=CVRPInstance.load, make_model_spec=make_model_spec, micro_size="6", load_cases=_load_cases,
    constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.cvrp.model_parts", make_model_spec(), "cvrp")
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.cvrp.native_parts"
PACK.bench_size = "x150"
PACK.variants = {"routes": (make_model_spec, "examples.cvrp.model_parts")}
