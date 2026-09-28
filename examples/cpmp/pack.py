"""`ProblemPack` del CPMP: lo que el framework recibe de este problema (ver `core.problem_pack`).

Solo el lado constructivo: el LLM genera puntajes (`--slots greedy_score`), cada uno entra
como `greedy_<nombre>` y `beam_<nombre>`, y el tuner elige constructor en el esqueleto
`CONSTRUCT`. Sin vista MIP, `--ref-time` del tuner no aplica.
"""

from __future__ import annotations

from random import Random

from core.problem_pack import ProblemPack

from .catalog import CONSTRUCTOR_SKELETONS, HANDWRITTEN, BestFirstConstructor
from .instance import CPMPInstance
from .llm_spec import make_contexts, make_spec
from .problem_model import CPMPModel


def parse_size(text: str) -> dict:
    """"SxH" (pilas × altura), p.ej. "6x6"."""
    S, H = (int(v) for v in text.lower().split("x"))
    return {"S": S, "H": H}


def make_instances(n: int, seed0: int, size: dict):
    """Al estilo CVS: todas las pilas con H − 2 contenedores, grupos distintos."""
    return [CPMPInstance.cvs_like(size["S"], size["H"], Random(seed0 + k)) for k in range(n)]


PACK = ProblemPack(
    name="cpmp",
    module="examples.cpmp",
    problem_factory=CPMPModel,
    handwritten=HANDWRITTEN,
    make_spec=make_spec,
    make_contexts=make_contexts,
    make_instances=make_instances,
    parse_size=parse_size,
    default_size="5x5",  # el respaldo neutral (best-first) ordena todas las de 5×5, no todas las de 6×6
    baseline_constructor=BestFirstConstructor,
    load_instance=CPMPInstance.load,
    constructor_skeletons=CONSTRUCTOR_SKELETONS,
    beam_constructors=True,
    skeletons=["CONSTRUCT"],
)
