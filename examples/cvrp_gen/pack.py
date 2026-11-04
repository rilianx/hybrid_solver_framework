"""`ProblemPack` del CVRP sin nada escrito a mano más allá de la instancia, la descripción, los casos y el modelo de
referencia en Python: el modelo C++ y los componentes los escribe el LLM (`native_parts.GENERATION`)."""

from __future__ import annotations

from core.problem_pack import ProblemPack
from examples.cvrp import model_parts
from examples.cvrp.pack import PACK as _CVRP
from core.packs import TrivialConstructor, parts_pack

_BASE = ProblemPack(
    name="cvrp_gen", module="examples.cvrp_gen", problem_factory=None, handwritten=[],
    make_instances=_CVRP.make_instances, parse_size=_CVRP.parse_size,
    default_size=_CVRP.default_size, baseline_constructor=None, load_instance=_CVRP.load_instance,
    make_model_spec=_CVRP.make_model_spec, micro_size=_CVRP.micro_size, load_cases=_CVRP.load_cases,
    constructor_skeletons=list(_CVRP.constructor_skeletons),
)
PACK = parts_pack(_BASE, model_parts, "examples.cvrp.model_parts", _CVRP.make_model_spec(), "cvrp_gen")
PACK.module = "examples.cvrp_gen"
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.cvrp_gen.native_parts"
PACK.bench_size = "x150"
PACK.variants = {"routes": (_CVRP.make_model_spec, "examples.cvrp.model_parts")}
