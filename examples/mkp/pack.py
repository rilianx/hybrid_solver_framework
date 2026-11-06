"""`ProblemPack` de la mochila multidimensional. Lo humano es la instancia, la descripción para el LLM, los casos de
prueba y el oráculo en Python (`model_parts`); el modelo C++, los componentes y la vista MIP los escribe el LLM
(`native_parts.GENERATION`)."""

from __future__ import annotations

from random import Random

from core.packs import TrivialConstructor, parts_pack
from core.problem_pack import ProblemPack

from . import model_parts
from .instance import MKPInstance
from .llm_spec import make_model_spec

SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]


def make_instances(n: int, seed0: int, size: dict):
    """Como las de Chu y Beasley (`MKPInstance.random`), con holgura 0.25, 0.5 y 0.75 en rotación; con `n<ítems>x<recursos>`
    (p.ej. `n100x5`), como las de ReEvo y MCTS-AHD (`MKPInstance.normalized`; otras semillas: no son esas instancias)."""
    if size.get("normalized"):
        return [MKPInstance.normalized(size["items"], size["resources"], Random(seed0 + k)) for k in range(n)]
    return [MKPInstance.random(size["items"], size["resources"], Random(seed0 + k), tightness=[0.25, 0.5, 0.75][k % 3])
            for k in range(n)]


def parse_size(text: str) -> dict:
    """`<ítems>x<recursos>`, p.ej. `250x10`; `n100x5`, normalizadas como las de ReEvo."""
    text = text.lower()
    norm = text.startswith("n")
    n, m = text.lstrip("n").split("x")
    return {"items": int(n), "resources": int(m), **({"normalized": True} if norm else {})}


def _load_cases():
    from .cases import load_cases

    return load_cases()


_BASE = ProblemPack(
    name="mkp", module="examples.mkp", problem_factory=None,
    make_instances=make_instances, parse_size=parse_size, default_size="100x5", baseline_constructor=None,
    load_instance=MKPInstance.load, make_model_spec=make_model_spec, micro_size="12x3", load_cases=_load_cases,
    constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.mkp.model_parts", make_model_spec(), "mkp")
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.mkp.native_parts"
PACK.bench_size = "250x10"
PACK.variants = {"binary": (make_model_spec, "examples.mkp.model_parts")}
# presupuesto por instancia (`--scale-budget`): proporcional a ítems·restricciones, 1 en 100×5
PACK.budget_scale = lambda inst: inst.n_items * inst.n_resources / 500
