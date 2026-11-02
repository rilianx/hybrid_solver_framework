"""`ProblemPack` del flow shop de permutación con makespan: el de `examples.flowshop` (instancias, tamaños, esqueletos)
con otro objetivo. Lo humano es la descripción para el LLM, los casos y el modelo de referencia (`model_parts`)."""

from __future__ import annotations

from core.problem_pack import ProblemPack
from examples.flowshop.instance import PFSPInstance
from examples.flowshop.pack import SKELETONS, make_instances, parse_size
from llm.cycle import TrivialConstructor, parts_pack

from . import model_parts
from .llm_spec import make_model_spec


def _load_cases():
    from .cases import load_cases

    return load_cases()


_BASE = ProblemPack(
    name="flowshop_cmax", module="examples.flowshop_cmax", problem_factory=None, handwritten=[], make_spec=None,
    make_contexts=None, make_instances=make_instances, parse_size=parse_size, default_size="50x10",
    baseline_constructor=None, load_instance=PFSPInstance.load, make_model_spec=make_model_spec, micro_size="6x3",
    load_cases=_load_cases, constructor_skeletons=SKELETONS,
)

PACK = parts_pack(_BASE, model_parts, "examples.flowshop_cmax.model_parts", make_model_spec(), "flowshop_cmax")
PACK.module = "examples.flowshop_cmax"
PACK.baseline_constructor = lambda: TrivialConstructor(model_parts)
PACK.native_module = "examples.flowshop_cmax.native_parts"
PACK.bench_size = "100x10"
# tiempo proporcional a n·m como en la literatura (n·m/2·t ms); 1 en el tamaño por defecto (50x10)
PACK.budget_scale = lambda inst: inst.n_jobs * inst.n_machines / 500
PACK.variants = {"permutation": (make_model_spec, "examples.flowshop_cmax.model_parts")}
