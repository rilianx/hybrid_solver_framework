"""Catálogo de referencia del CPMP (`HANDWRITTEN`). Registrar, envolver puntajes y cargar
generados es genérico (`llm.catalog`); aquí solo se ata al pack del CPMP.

Sin vecindarios ni vista MIP todavía, el único esqueleto es `CONSTRUCT` (solo el
constructor): el tuner elige entre constructores (`best_first`, `frg`, `greedy_<puntaje>`,
`beam_<puntaje>`, `greedy_phased`, `beam_phased`) y sus parámetros.
"""

from __future__ import annotations

from pathlib import Path
from random import Random

from core.component import ComponentRegistry
from llm import catalog as _catalog
from llm.generator import GeneratedComponent

from .construction import DestinationRank, FRGConstructor, FRGPolicy
from .phases import BGFill, ReduceStack

CONSTRUCTOR_SKELETONS = ["CONSTRUCT"]


class BestFirstConstructor:
    """Partida trivial: el respaldo de la vista desde el layout vacío (búsqueda best-first
    por mal puestos, sin reglas de ninguna heurística)."""

    def __init__(self, problem=None):
        self.problem = problem

    def build(self, inst, rng: Random):
        from .problem_model import CPMPModel

        P = self.problem if self.problem is not None else CPMPModel(inst)
        view = P.construction_view(inst)
        return view.complete(view.empty(), rng)


HANDWRITTEN = [
    ({"name": "best_first", "slot": "constructor", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: BestFirstConstructor(problem)),
    ({"name": "frg", "slot": "constructor", "compatible_skeletons": CONSTRUCTOR_SKELETONS,
      "params": {"prevent": {"type": "bool"}, "assignment": {"type": "cat", "values": ["fallback", "always", "never"]}}},
     lambda problem, prevent=True, assignment="fallback": FRGConstructor(problem, prevent=prevent, assignment=assignment)),
    ({"name": "frg_policy", "slot": "construction_policy", "compatible_skeletons": CONSTRUCTOR_SKELETONS,
      "params": {"prevent": {"type": "bool"}}},
     lambda problem, prevent=True: FRGPolicy(problem, prevent=prevent)),
    ({"name": "destination_rank", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: DestinationRank(problem)),
    # FRG como fases (`core.phases`): con `greedy_phased` / `beam_phased` el tuner elige cuántas y cuáles;
    # por defecto las dos, en este orden, que es FRG sin asignación
    (dict(BGFill.COMPONENT, compatible_skeletons=CONSTRUCTOR_SKELETONS), lambda problem, prevent=True: BGFill(problem, prevent)),
    (dict(ReduceStack.COMPONENT, compatible_skeletons=CONSTRUCTOR_SKELETONS), lambda problem, r=1: ReduceStack(problem, r)),
]


def build_registry(generated: list[GeneratedComponent] | None = None, handwritten: bool = True,
                   exclude_slots: set[str] | None = None) -> ComponentRegistry:
    from .pack import PACK

    return _catalog.build_registry(PACK, generated, handwritten, exclude_slots)


def load_generated(workspace: str | Path = "generated/cpmp", revalidate: bool = True, verbose: bool = True,
                   combination: bool = False) -> list[GeneratedComponent]:
    from .pack import PACK

    return _catalog.load_generated(PACK, workspace, revalidate, verbose, combination)
