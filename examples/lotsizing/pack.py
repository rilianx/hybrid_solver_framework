"""`ProblemPack` del CLSP (lot sizing capacitado multi-ítem). Lo humano es la instancia (con el generador al estilo
Trigeiro), la descripción para el LLM, los casos de prueba y el modelo de referencia en Python (`model_parts`, oráculo
y vista MIP con un grupo de setups por período); el modelo C++ y los componentes los escribe el LLM
(`native_parts.GENERATION`). Las destrucciones del sub-MIP de HYB son las genéricas de `core.packs` (ventana de
períodos y setups al azar)."""

from __future__ import annotations

from random import Random

from core.packs import TrivialConstructor, parts_pack
from core.problem_pack import ProblemPack

from . import model_parts
from .instance import CLSPInstance
from .llm_spec import make_model_spec

SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB", "GRASP"]


def make_instances(n: int, seed0: int, size: dict, utilization: float = 0.95, tbo: float = 3.0):
    return [CLSPInstance.trigeiro(size["items"], size["periods"], Random(seed0 + k), utilization=utilization, tbo=tbo)
            for k in range(n)]


def _load_cases():
    from .cases import load_cases

    return load_cases()


def parse_size(text: str) -> dict:
    items, periods = text.lower().split("x")
    return {"items": int(items), "periods": int(periods)}


_BASE = ProblemPack(
    name="clsp", module="examples.lotsizing", problem_factory=None,
    make_instances=make_instances, parse_size=parse_size, default_size="10x15", baseline_constructor=None,
    load_instance=CLSPInstance.load, make_model_spec=make_model_spec, micro_size="3x4", load_cases=_load_cases,
    constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.lotsizing.model_parts", make_model_spec(), "clsp")
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.lotsizing.native_parts"
PACK.variants = {"setups": (make_model_spec, "examples.lotsizing.model_parts")}
# presupuesto por instancia (`--scale-budget`): proporcional a ítems·períodos, 1 en 20×20
PACK.budget_scale = lambda inst: inst.n_items * inst.n_periods / 400
