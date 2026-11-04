"""`ProblemPack` del job shop sin nada escrito a mano más allá de la instancia, la descripción, los casos y el modelo de
referencia en Python: el modelo C++ y los componentes los escribe el LLM (`native_parts.GENERATION`)."""

from __future__ import annotations

from dataclasses import replace

from examples.jobshop import model_parts
from examples.jobshop.instance import JSSPInstance
from examples.jobshop.llm_spec import make_model_spec
from examples.jobshop.pack import _BASE
from core.packs import TrivialConstructor, parts_pack

_GEN = replace(_BASE, name="jobshop_gen", module="examples.jobshop_gen", handwritten=[], baseline_constructor=None)
PACK = parts_pack(_GEN, model_parts, "examples.jobshop.model_parts", make_model_spec(), "jobshop_gen")
PACK.module = "examples.jobshop_gen"
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.jobshop_gen.native_parts"
PACK.bench_size = "20x15"
PACK.load_instance = JSSPInstance.load
PACK.variants = {"sequences": (make_model_spec, "examples.jobshop.model_parts")}
