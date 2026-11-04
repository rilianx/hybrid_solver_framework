"""El pack de un problema a partir de sus piezas de referencia (`model_parts`): el `ProblemModel` (`PartsModel`), el
catálogo mínimo (partidas trivial y al azar), los contextos de validación de componentes y el registro de problemas."""

from __future__ import annotations

import importlib
from random import Random
from typing import Any

from core.model_parts import PartsModel
from core.problem_pack import ProblemPack

PACKS = {"clsp": "examples.lotsizing.pack", "cvrp": "examples.cvrp.pack", "jobshop": "examples.jobshop.pack",
         "flowshop": "examples.flowshop.pack", "flowshop_cmax": "examples.flowshop_cmax.pack",
         "jobshop_gen": "examples.jobshop_gen.pack", "cvrp_gen": "examples.cvrp_gen.pack"}


def base_pack(problem: str) -> ProblemPack:
    return importlib.import_module(PACKS[problem]).PACK


class TrivialConstructor:
    """La solución trivial de las piezas: partida de referencia y normalizador del tuner."""

    def __init__(self, parts):
        self.parts = parts

    def build(self, inst, rng: Random):
        return self.parts.trivial_solution(inst)


class RandomConstructor:
    def __init__(self, parts):
        self.parts = parts

    def build(self, inst, rng: Random):
        return self.parts.random_solution(inst, rng)


def _handwritten(parts, skeletons: list[str]) -> list[tuple[dict, Any]]:
    return [
        ({"name": "trivial", "slot": "constructor", "compatible_skeletons": skeletons, "params": {}},
         lambda problem: TrivialConstructor(parts)),
        ({"name": "random", "slot": "constructor", "compatible_skeletons": skeletons, "params": {}},
         lambda problem: RandomConstructor(parts)),
    ]


def parts_contexts(base: ProblemPack, parts, n_contexts: int = 2, strict: bool = True, reference_free: bool = True,
                   combination: bool = False, pack: ProblemPack | None = None):
    from core.validation import ValidationContext
    from core.validation.base import DiversityProbe

    def good_start(problem, inst):
        """Partida con estructura: la mejor entre la trivial y unas al azar (la trivial sola puede ser
        degenerada: una ruta por cliente, corrida 20)."""
        cands = [parts.trivial_solution(inst)] + [parts.random_solution(inst, Random(s)) for s in range(8)]
        feas = [c for c in cands if problem.is_feasible(c)] or cands
        return min(feas, key=problem.objective)

    scale = base.make_instances(1, 100, base.parse_size(base.default_size))[0]
    probe_problem = PartsModel(parts, scale)
    probe = DiversityProbe(problem=probe_problem, solution=good_start(probe_problem, scale), max_similarity=0.8)
    combo = None
    if combination and pack is not None:
        combo = _combination_probe(pack, probe)
    micro = base.make_instances(n_contexts, 7, base.parse_size(base.micro_size or base.default_size))
    contexts = []
    for inst in micro:
        problem = PartsModel(parts, inst)
        contexts.append(ValidationContext(
            problem=problem,
            instances=[inst],
            trivial_solutions=[parts.trivial_solution(inst)],
            baseline_constructor=RandomConstructor(parts),
            mip_time_limit=10.0,
            max_moves_checked=30,
            require_improving_from_start=strict,
            diversity_probe=probe,
            combination=combo,
        ))
    return contexts


def _combination_probe(pack: ProblemPack, probe):
    from core.assembler import Assembler
    from core.component import ComponentSpec
    from core.validation.combination import CombinationProbe

    from core.catalog import build_registry

    def assembler_for(slot, components):
        registry = build_registry(pack, exclude_slots={slot})
        names = []
        for component, factory in components:
            spec = dict(component)
            spec.pop("combination_gains", None)
            registry.register(ComponentSpec.from_dict(spec, factory))
            names.append(spec["name"])
        assembler = Assembler(problem_factory=pack.problem_factory, registry=registry)
        assembler.probe_component = names[0]
        return assembler

    return CombinationProbe(instance=probe.problem.inst, assembler_for=assembler_for, starts=["trivial", "random"], budget=1.0)


def parts_pack(base: ProblemPack, parts, parts_import: str, model_spec, name: str) -> ProblemPack:
    """El pack de una representación: instancias y casos del pack base; modelo, catálogo mínimo y
    especificación para los componentes, de las piezas."""
    pack = ProblemPack(
        name=name,
        module=base.module,
        problem_factory=lambda inst: PartsModel(parts, inst),
        handwritten=_handwritten(parts, list(base.constructor_skeletons)),
        make_contexts=lambda **kw: None,  # se reemplaza abajo (necesita el pack para la sonda de combinación)
        make_instances=base.make_instances,
        parse_size=base.parse_size,
        default_size=base.default_size,
        baseline_constructor=lambda: TrivialConstructor(parts),
        load_instance=base.load_instance,
        make_model_spec=lambda: model_spec,
        micro_size=base.micro_size,
        load_cases=base.load_cases,
        constructor_skeletons=list(base.constructor_skeletons),
    )
    pack.make_contexts = lambda n_contexts=2, strict=True, reference_free=True, combination=False: parts_contexts(
        base, parts, n_contexts, strict, reference_free, combination, pack)
    return pack
